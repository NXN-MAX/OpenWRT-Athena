import {cpSync,mkdtempSync,mkdirSync,readFileSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve,join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const base=resolve(import.meta.dirname,'..'),version=JSON.parse(readFileSync(join(base,'package.json'))).version;
if(readFileSync(join(base,'htdocs/luci-static/athena/release-version'),'utf8').trim()!==version)throw new Error('Build the current version before packing');
const output=resolve(process.argv[2]||join(base,'dist'));mkdirSync(output,{recursive:true});
const work=mkdtempSync(join(tmpdir(),'athena-release-')),stage=join(work,'luci-theme-athena');mkdirSync(stage);
try {
 for(const path of ['htdocs','ucode','root','licenses','LICENSE','NOTICE','README.md','Makefile'])cpSync(join(base,path),join(stage,path),{recursive:true,filter:src=>!src.endsWith('/.DS_Store')&&!src.includes('/branding/')});
 mkdirSync(join(stage,'scripts'));cpSync(join(base,'scripts/install.sh'),join(stage,'scripts/install.sh'));
 const name=`luci-theme-athena-${version}.tar.gz`,archive=join(output,name);
 const result=spawnSync('tar',['-czf',archive,'-C',work,'luci-theme-athena'],{stdio:'inherit',env:{...process.env,COPYFILE_DISABLE:'1'}});if(result.status)throw new Error('Archive creation failed');
 writeFileSync(join(output,name+'.sha256'),createHash('sha256').update(readFileSync(archive)).digest('hex')+'  '+name+'\n');
 console.log(archive);
} finally {rmSync(work,{recursive:true,force:true});}
