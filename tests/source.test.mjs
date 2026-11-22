import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync,readdirSync } from 'node:fs';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('native package contains no React or legacy theme runtime',()=>{
 const pkg=JSON.parse(read('package.json'));assert.deepEqual(Object.keys(pkg.dependencies).sort(),['@heroui/styles','tailwindcss']);
 for(const path of ['htdocs/luci-static/resources/athena/ui.js','htdocs/luci-static/resources/menu-athena.js','src/styles.css'])assert.doesNotMatch(read(path),/ReactDOM|createRoot|argon|app\.js/);
});
test('theme uses ucode and allows only one LuCI core script from stock wrapper',()=>{
 const files=readdirSync(new URL('../ucode/template/themes/athena/',import.meta.url));assert(files.includes('header.ut'));assert(files.includes('sysauth.ut'));
 const header=read('ucode/template/themes/athena/header.ut');assert.doesNotMatch(header,/resource.*\/luci\.js/);assert.match(header,/cbi\.js/);
 assert.doesNotMatch(read('Makefile'),/luci-compat|lua/);
});
test('native source controls remain original nodes',()=>{
 const source=read('htdocs/luci-static/resources/athena/ui.js');assert.doesNotMatch(source,/cloneNode|createRoot|innerHTML\s*=/);
 assert.match(source,/wrapper\.append\(node, track\)/);assert.match(source,/scroll\.append\(table\)/);
});
test('upload permission is scoped to random Athena temporary files',()=>{
 const acl=JSON.parse(read('root/usr/share/rpcd/acl.d/luci-theme-athena.json'))['luci-theme-athena'];assert.deepEqual(Object.keys(acl.write.file),['/tmp/athena-upload-*.tmp']);assert(!acl.write.ubus.file);
});
test('native settings use the canonical renamed route',()=>{
 const menu=JSON.parse(read('root/usr/share/luci/menu.d/luci-theme-athena.json'));
 assert.equal(menu['admin/system/athena'].action.path,'athena-config');
 assert.deepEqual(menu['admin/system/Athena-config'].action,{type:'alias',path:'admin/system/athena'});
 const source=read('htdocs/luci-static/resources/view/athena-config.js');assert.doesNotMatch(source,/wallpaper|blur|opacity|updateTheme|bing|unsplash|dark_color/);
});
