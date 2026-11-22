#!/usr/bin/env python3
"""Sign verified release packages on a trusted SSH host and optionally publish feeds."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import uuid

BASE = Path(__file__).resolve().parent.parent
REMOTE = 'git@github.com:NXN-MAX/OpenWRT-Athena.git'
spec = importlib.util.spec_from_file_location('feed_index', BASE / 'scripts/feed-index.py')
index_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(index_module)


def run(command, **kwargs):
    return subprocess.run(command, check=True, **kwargs)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_inputs(source, version, keys):
    if not keys.is_dir() or keys.stat().st_mode & 0o077:
        raise ValueError('Signing key directory must have mode 0700')
    expected = [f'luci-theme-athena_{version}-r1_all.ipk', f'luci-theme-athena-{version}-r1.apk']
    checksums = {}
    for line in (source / 'SHA256SUMS').read_text().splitlines():
        sha, name = line.split(maxsplit=1)
        if not re.fullmatch(r'[a-f0-9]{64}', sha):
            raise ValueError('Invalid release checksum')
        checksums[name.strip()] = sha
    for name in expected:
        file = source / name
        if file.is_symlink() or not file.is_file() or digest(file) != checksums.get(name):
            raise ValueError('Missing package or checksum mismatch: ' + name)
    index, control = index_module.package_index(source / expected[0])
    if control.get('Version') != version + '-r1':
        raise ValueError('IPK version mismatch')
    for private, public in [('opkg.sec', 'athena-opkg.pub'), ('apk.pem', 'athena-apk.pub.pem')]:
        secret = keys / private
        if secret.is_symlink() or not secret.is_file() or secret.stat().st_mode & 0o077:
            raise ValueError('Signing private keys must be regular files with mode 0600')
        if not (BASE / 'keys' / public).is_file():
            raise ValueError('Pinned public key is missing')
    return expected, index


def sign(source, output, version, keys, ssh, apk_tool):
    expected, index = check_inputs(source, version, keys)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output must be empty; old feed artifacts will not be overwritten')
    remote_dir = '/tmp/athena-feed-sign-' + uuid.uuid4().hex
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode='w:gz') as tar:
        for name, destination in [(expected[0], 'public/24.10/all/'), (expected[1], 'public/25.12/noarch/')]:
            tar.add(source / name, destination + name, recursive=False)
        for name in ['opkg.sec', 'apk.pem']:
            tar.add(keys / name, '.private/' + name, recursive=False)
        for name in ['athena-opkg.pub', 'athena-apk.pub.pem']:
            tar.add(BASE / 'keys' / name, 'public/keys/' + name, recursive=False)
        for name, data in [('public/24.10/all/Packages', index),
                           ('public/24.10/all/Packages.gz', __import__('gzip').compress(index, mtime=0))]:
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
        tar.add(BASE / 'scripts/feed-sign-remote.sh', 'sign.sh', recursive=False)
    quoted = shlex.quote(remote_dir)
    command = ('set -eu; umask 077; mkdir ' + quoted + '; trap ' +
               shlex.quote('rm -rf ' + quoted) + ' EXIT; tar -xzf - -C ' + quoted +
               '; sh ' + shlex.quote(remote_dir + '/sign.sh') + ' ' + quoted + ' ' + shlex.quote(apk_tool))
    # Key material only travels over encrypted SSH stdin and is cleaned from /tmp on exit.
    result = run([str(ssh), command], input=payload.getvalue(), stdout=subprocess.PIPE)
    output.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(result.stdout)) as tar:
        for entry in tar.getmembers():
            name = entry.name.removeprefix('./')
            if not name or entry.isdir():
                continue
            if not entry.isfile() or name.startswith('/') or '..' in Path(name).parts or '.private' in Path(name).parts:
                raise ValueError('Invalid signing output path')
            if not (name.startswith(('24.10/all/', '25.12/noarch/', 'keys/')) or name in ['package-info.json', 'opkg-fingerprint.txt']):
                raise ValueError('Unexpected signing output')
            target = output / name; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(tar.extractfile(entry).read()); target.chmod(0o644)
    info = json.loads((output / 'package-info.json').read_text())['info']
    if (info['name'], info['version'], info['arch']) != ('luci-theme-athena', version + '-r1', 'noarch'):
        raise ValueError('APK metadata mismatch')
    (output / 'package-info.json').unlink()
    for name in ['athena-opkg.pub', 'athena-apk.pub.pem']:
        if (output / 'keys' / name).read_bytes() != (BASE / 'keys' / name).read_bytes():
            raise ValueError('Signing host public key mismatch')
    import base64
    pub = ''.join((BASE / 'keys/athena-opkg.pub').read_text().splitlines()[1:])
    expected_fingerprint = base64.b64decode(pub)[2:10].hex()
    if (output / 'opkg-fingerprint.txt').read_text().strip() != expected_fingerprint:
        raise ValueError('Opkg public key fingerprint mismatch')
    manifest = {'schema': 'athena-feed-v1', 'version': version, 'third_party': True,
                'opkg_fingerprint': expected_fingerprint,
                'files': {str(p.relative_to(output)): digest(p) for p in sorted(output.rglob('*')) if p.is_file()}}
    (output / 'feed.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / 'README.md').write_text('# Athena signed package feed\n\n'
        'Independent third-party feed, not an official OpenWrt repository.\n\n'
        'Installation and public-key fingerprints: https://github.com/NXN-MAX/OpenWRT-Athena/blob/main/doc/signed-feed.md\n')
    return manifest


def publish(output):
    with tempfile.TemporaryDirectory(prefix='athena-feed-publish-') as directory:
        repo = Path(directory)
        run(['git', 'init', '-q', str(repo)])
        run(['git', '-C', str(repo), 'remote', 'add', 'origin', REMOTE])
        existing = subprocess.run(['git', 'ls-remote', '--exit-code', REMOTE, 'refs/heads/feeds'], stdout=subprocess.DEVNULL)
        if existing.returncode == 0:
            run(['git', '-C', str(repo), 'fetch', '--depth=1', 'origin', 'feeds'])
            run(['git', '-C', str(repo), 'checkout', '-b', 'feeds', 'FETCH_HEAD'])
            for name in ['athena-opkg.pub', 'athena-apk.pub.pem']:
                old = repo / 'keys' / name
                if not old.is_file() or old.read_bytes() != (output / 'keys' / name).read_bytes():
                    raise ValueError('Published keys differ; explicit key rotation is required')
        elif existing.returncode == 2:
            run(['git', '-C', str(repo), 'checkout', '--orphan', 'feeds'])
        else:
            raise RuntimeError('Cannot inspect the remote feeds branch')
        shutil.copytree(output, repo, dirs_exist_ok=True)
        # Previous package filenames remain available for cached, verified indexes.
        run(['git', '-C', str(repo), 'add', '24.10', '25.12', 'keys', 'feed.json', 'README.md', 'opkg-fingerprint.txt'])
        dirty = subprocess.run(['git', '-C', str(repo), 'diff', '--cached', '--quiet'])
        if dirty.returncode == 0:
            print('Feed already matches the signed output'); return
        run(['git', '-C', str(repo), '-c', 'user.name=Athena feed publisher', '-c',
             'user.email=29735419+NXN-MAX@users.noreply.github.com', 'commit', '-m',
             'Publish signed Athena feed ' + json.loads((output / 'feed.json').read_text())['version']])
        run(['git', '-C', str(repo), 'push', 'origin', 'HEAD:refs/heads/feeds'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--version', required=True)
    parser.add_argument('--key-dir', type=Path, default=Path.home() / '.config/athena/signing')
    parser.add_argument('--ssh', type=Path, required=True, help='Trusted signing-host SSH wrapper')
    parser.add_argument('--apk-tool', default='/tmp/athena-feed-tools/sbin/apk.static', help='Full apk v3 tool on signing host')
    parser.add_argument('--publish', action='store_true', help='Push the verified public tree over GitHub SSH')
    args = parser.parse_args()
    if not re.fullmatch(r'\d+\.\d+\.\d+', args.version):
        parser.error('Only stable X.Y.Z versions are supported')
    manifest = sign(args.release.resolve(), args.output.resolve(), args.version, args.key_dir.resolve(), args.ssh.resolve(), args.apk_tool)
    print(json.dumps({'version': manifest['version'], 'opkg_fingerprint': manifest['opkg_fingerprint'], 'files': len(manifest['files'])}))
    if args.publish:
        publish(args.output.resolve())


if __name__ == '__main__':
    main()
