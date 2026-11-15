#!/usr/bin/env python3
"""Exercise the real updater in an isolated /tmp tree on an OpenWrt test device."""
from pathlib import Path, PurePosixPath
import hashlib, io, json, os, shlex, shutil, subprocess, sys, tarfile, tempfile

base = Path(__file__).resolve().parents[1]
ssh_command = shlex.split(os.environ.get('ATHENA_SSH', str(base.parent / 'scripts/ssh.sh')))
remote = '/tmp/athena-updater-test'
def ssh(command, data=None):
    result = subprocess.run(ssh_command + [command], input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(result.stdout.decode(errors='replace') + result.stderr.decode(errors='replace'))
    return result.stdout.decode().strip()
def send(path, data):
    ssh('cat > ' + shlex.quote(path), data)
def check(ok, message):
    if not ok: raise AssertionError(message)
    print('PASS:', message, flush=True)

ssh(f'mkdir -p {remote}/bin')
try:
    source = (base / 'root/usr/share/rpcd/ucode/luci.athena').read_text()
    pure = source[source.index('function currentVersion()'):source.index('function checkUpdate()')]
    pure = pure.replace('/www/luci-static/athena/release-version', remote + '/release-version')
    send(remote + '/release-version', b'2.0.0\n')
    test = '''
const prefix='https://github.com/NXN-MAX/OpenWRT-Athena/releases/download/v2.0.1/';
let asset={name:'luci-theme-athena-2.0.1.tar.gz',state:'uploaded',size:1024,digest:'sha256:'+'a' * 64,browser_download_url:prefix+'luci-theme-athena-2.0.1.tar.gz'};
let release={tag_name:'v2.0.1',draft:false,prerelease:false,assets:[asset]};
function check(ok,label){if(!ok)die(label);print('PASS: ',label,'\\n');}
check(newer('2.0.10','2.0.2') && !newer('2.0.0','2.0.0'),'numeric semantic version ordering');
check(parseRelease(release).available,'verified newer official asset');
asset.browser_download_url='https://example.com/package.tar.gz';check(!parseRelease(release).available,'reject foreign asset URL');asset.browser_download_url=prefix+asset.name;
asset.digest=null;check(!parseRelease(release).available,'reject missing digest');asset.digest='sha256:'+'a' * 64;
asset.size=9*1024*1024;check(!parseRelease(release).available,'reject oversized archive');asset.size=1024;
release.prerelease=true;check(parseRelease(release).result==1,'reject prerelease');release.prerelease=false;
release.tag_name='v2.0.1;id';check(parseRelease(release).result==1,'reject injected tag');
release.tag_name='v1.9.9';check(!parseRelease(release).available,'reject downgrade');
'''
    test = test.replace("'a' * 64", repr('a' * 64))
    send(remote + '/release-tests.uc', ('import {readfile} from "fs";\n' + pure + test).encode())
    print(ssh(f'ucode {remote}/release-tests.uc'), flush=True)
    # Exercise the actual asynchronous RPC launch in a private namespace. The
    # substitute helper only writes test status; it never installs any files.
    release={'result':0,'available':True,'tag':'v2.0.1','url':'https://github.com/NXN-MAX/OpenWRT-Athena/releases/download/v2.0.1/luci-theme-athena-2.0.1.tar.gz','digest':'a'*64,'size':1024}
    begin=source.index('function checkUpdate()');end=source.index('function updateStatus(')
    launch=source[:begin]+'function checkUpdate(){return '+json.dumps(release)+';}\n'+source[end:]
    launch=launch.replace('/var/run/athena-update',remote+'/rpc-state').replace('/usr/libexec/athena-update',remote+'/launch-helper')
    send(remote+'/launch-helper',('#!/bin/sh\nprintf \'{"phase":"complete","version":"2.0.1"}\\n\' > '+remote+'/rpc-state/"$1".json\n').encode())
    ssh('chmod +x '+remote+'/launch-helper');send(remote+'/launch.uc',launch.encode())
    invocation='const api=loadfile("'+remote+'/launch.uc")()["luci.athena"];'
    started=json.loads(ssh('ucode -e '+shlex.quote(invocation+'print(sprintf("%J",api.start_update.call({args:{tag:"v2.0.1"}})));')))
    check(started.get('result')==0 and started.get('job'),'native RPC starts an asynchronous job without installing files')
    status=json.loads(ssh('ucode -e '+shlex.quote(invocation+'print(sprintf("%J",api.update_status.call({args:{job:"'+started['job']+'"}})));')))
    check(status.get('phase')=='complete','native RPC reads the private job status')
    again=json.loads(ssh('ucode -e '+shlex.quote(invocation+'print(sprintf("%J",api.start_update.call({args:{tag:"v2.0.1"}})));')))
    check(again.get('result')==1 and 'already running' in again.get('error',''),'native RPC serializes concurrent updates')
    helper = (base / 'root/usr/libexec/athena-update').read_text()
    helper = helper.replace('/tmp/athena-update', remote + '/work').replace('/var/run/athena-update', remote + '/state').replace('/usr/bin/curl', remote + '/bin/curl').replace("target_root=''", f"target_root='{remote}/installed'")
    send(remote + '/updater', helper.encode())
    send(remote + '/bin/curl', b'''#!/bin/sh
while [ "$#" -gt 0 ]; do
 if [ "$1" = -o ]; then shift; output=$1; fi
 shift
done
/bin/cp "$ATHENA_TEST_ARCHIVE" "$output"
''')
    send(remote + '/bin/cp', (f'''#!/bin/sh
case "$*" in
 *"{remote}/installed/"*".next"*)
  if [ "$ATHENA_TEST_FAIL" = 1 ] && [ ! -f {remote}/failed-once ]; then touch {remote}/failed-once; exit 1; fi ;;
esac
exec /bin/cp "$@"
''').encode())
    ssh(f'chmod +x {remote}/updater {remote}/bin/*')
    with tempfile.TemporaryDirectory(prefix='athena-updater-fixture-') as folder:
        folder = Path(folder)
        version=json.loads((base/'package.json').read_text())['version']
        package_path=Path(os.environ.get('ATHENA_TEST_PACKAGE',base/'dist'/('luci-theme-athena-'+version+'.tar.gz')))
        with tarfile.open(package_path) as package:
            for member in package.getmembers():
                parts=PurePosixPath(member.name).parts
                assert parts and parts[0]=='luci-theme-athena' and '..' not in parts and (member.isdir() or member.isfile())
            package.extractall(folder)
        theme = folder / 'luci-theme-athena'
        (theme / 'htdocs/luci-static/athena/release-version').write_text('2.0.1\n')
        branding = theme / 'htdocs/luci-static/athena/branding'
        branding.mkdir(exist_ok=True);(branding / 'keep.txt').write_text('must not replace custom asset')
        archive = folder / 'fixture.tar.gz'
        with tarfile.open(archive,'w:gz') as package: package.add(theme,arcname='luci-theme-athena')
        valid = archive.read_bytes()
        def run(data, fail=False, bad_digest=False):
            ssh(f'rm -rf {remote}/installed {remote}/state/lock; rm -f {remote}/failed-once; mkdir -p {remote}/installed/www/luci-static/athena/branding {remote}/installed/etc/config {remote}/state/lock')
            send(remote + '/installed/www/luci-static/athena/athena.css', b'OLD CSS')
            send(remote + '/installed/www/luci-static/athena/release-version', b'2.0.0\n')
            send(remote + '/installed/www/luci-static/athena/branding/keep.txt', b'CUSTOM ASSET')
            send(remote + '/installed/etc/config/athena', b'CUSTOM SETTINGS')
            job='12345678-1234-1234-1234-123456789abc';send(remote+'/state/lock/job',job.encode())
            send(remote+'/fixture.tar.gz',data)
            digest='0'*64 if bad_digest else hashlib.sha256(data).hexdigest()
            command=f'PATH={remote}/bin:$PATH ATHENA_TEST_FAIL={1 if fail else 0} ATHENA_TEST_ARCHIVE={remote}/fixture.tar.gz {remote}/updater {job} v2.0.1 https://github.com/NXN-MAX/OpenWRT-Athena/releases/download/v2.0.1/luci-theme-athena-2.0.1.tar.gz {digest} >{remote}/test.log 2>&1; cat {remote}/state/{job}.json'
            result=json.loads(ssh(command));result['log']=ssh('cat '+remote+'/test.log');return result
        result=run(valid)
        check(result['phase']=='complete','install verified archive in isolated target: '+result['log'])
        check(ssh(f'cat {remote}/installed/etc/config/athena')=='CUSTOM SETTINGS','preserve theme settings')
        check(ssh(f'cat {remote}/installed/www/luci-static/athena/branding/keep.txt')=='CUSTOM ASSET','preserve uploaded assets')
        check(ssh(f'test -s {remote}/installed'+result['backup']+' && printf yes')=='yes','create persistent rollback archive before install')
        backup_types=ssh(f'tar -tvzf {remote}/installed'+result['backup'])
        check(all(line.startswith('-') for line in backup_types.splitlines()),'backup excludes system-directory permission records')
        mode_script='import {lstat} from "fs"; print(sprintf("%o",lstat("'+remote+'/installed/www/luci-static/athena/icons").mode & 0777));'
        check(ssh('ucode -e '+shlex.quote(mode_script))=='755','new static directories remain web-readable')
        check(run(valid,bad_digest=True)['phase']=='failed','reject wrong SHA256 before install')
        result=run(valid,fail=True)
        check(result['phase']=='rolled_back','restore previous theme after interrupted copy')
        check(ssh(f'cat {remote}/installed/www/luci-static/athena/athena.css')=='OLD CSS','rollback restores original content')
        for name,kind in [('traversal','../escape'),('symlink','luci-theme-athena/evil')]:
            buffer=io.BytesIO()
            with tarfile.open(fileobj=buffer,mode='w:gz') as package:
                info=tarfile.TarInfo(kind)
                if name=='symlink': info.type=tarfile.SYMTYPE;info.linkname='/etc/config/system';package.addfile(info)
                else: info.size=1;package.addfile(info,io.BytesIO(b'x'))
            check(run(buffer.getvalue())['phase']=='failed','reject archive '+name)
finally:
    ssh('rm -rf ' + remote)
