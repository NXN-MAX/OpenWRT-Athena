import {readFileSync, writeFileSync} from 'node:fs';
import {resolve, join} from 'node:path';
import {createHash} from 'node:crypto';

const directory = resolve(process.argv[2] || 'dist');
const version = process.argv[3] || JSON.parse(readFileSync(new URL('../package.json', import.meta.url))).version;
if (!/^\d+\.\d+\.\d+$/.test(version)) throw new Error('Invalid stable release version');
const name = `luci-theme-athena-${version}.tar.gz`;
const archive = readFileSync(join(directory, name));
if (!archive.length || archive.length > 8 * 1024 * 1024) throw new Error('Invalid release archive size');
const manifest = {
  schema: 'athena-release-v1', tag_name: `v${version}`, draft: false, prerelease: false,
  assets: [{name, state: 'uploaded', size: archive.length,
    digest: `sha256:${createHash('sha256').update(archive).digest('hex')}`,
    browser_download_url: `https://github.com/NXN-MAX/OpenWRT-Athena/releases/download/v${version}/${name}`}]
};
writeFileSync(join(directory, 'athena-release.json'), JSON.stringify(manifest, null, 2) + '\n');
console.log(join(directory, 'athena-release.json'));
