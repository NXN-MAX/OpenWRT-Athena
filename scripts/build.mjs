import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, readdirSync, statSync, chmodSync } from 'node:fs';
import { createHash } from 'node:crypto';
const result = spawnSync('node_modules/.bin/tailwindcss', ['-i', 'src/styles.css', '-o', 'htdocs/luci-static/athena/athena.css', '--minify'], { stdio: 'inherit' });
if (result.status) process.exit(result.status);
// Source exports and browser uploads may drop executable file modes.
for (const file of ['root/etc/uci-defaults/30_luci-theme-athena', 'root/usr/libexec/athena-update', 'scripts/install.sh', 'scripts/test-device.sh']) chmodSync(file, 0o755);
const walk = dir => readdirSync(dir).sort().flatMap(name => { const path = `${dir}/${name}`; return statSync(path).isDirectory() ? walk(path) : [path]; });
const files = [...walk('htdocs'), ...walk('ucode'), ...walk('root')];
for (const file of files.filter(file => file.endsWith('.js'))) new Function(readFileSync(file, 'utf8'));
const sprite = readFileSync('htdocs/luci-static/athena/icons/sprite.svg', 'utf8');
for (const match of sprite.matchAll(/<symbol id="([^"]+)" viewBox="([^"]+)">([\s\S]*?)<\/symbol>/g))
  writeFileSync(`htdocs/luci-static/athena/icons/${match[1]}.svg`, `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${match[2]}">${match[3]}</svg>`);
const css = readFileSync('htdocs/luci-static/athena/athena.css');
const releaseVersion = JSON.parse(readFileSync('package.json', 'utf8')).version;
if (!/^\d+\.\d+\.\d+$/.test(releaseVersion) || !readFileSync('Makefile','utf8').includes('PKG_VERSION:='+releaseVersion)) throw new Error('package.json and Makefile versions must match');
writeFileSync('htdocs/luci-static/athena/release-version', releaseVersion+'\n');
writeFileSync('htdocs/luci-static/athena/version', createHash('sha256').update(css).update(files.filter(f => f.endsWith('.js')).map(f => readFileSync(f, 'utf8')).join('\n')).update(readFileSync('htdocs/luci-static/athena/login.svg')).digest('hex').slice(0, 12));
console.log(`Athena native assets built; CSS ${Math.round(css.length / 1024)} KiB; no JavaScript runtime bundle.`);
