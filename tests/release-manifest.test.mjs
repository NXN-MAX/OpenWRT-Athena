import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, writeFileSync, readFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';

test('release manifest describes the exact published archive and rejects invalid versions', () => {
  const dir = mkdtempSync(join(tmpdir(), 'athena-manifest-test-'));
  try {
    const bytes = Buffer.from('release archive fixture');
    writeFileSync(join(dir, 'luci-theme-athena-2.0.1.tar.gz'), bytes);
    const run = version => spawnSync(process.execPath, ['scripts/release-manifest.mjs', dir, version]);
    assert.equal(run('2.0.1').status, 0);
    const data = JSON.parse(readFileSync(join(dir, 'athena-release.json')));
    assert.equal(data.schema, 'athena-release-v1');
    assert.equal(data.tag_name, 'v2.0.1');
    assert.equal(data.draft, false); assert.equal(data.prerelease, false);
    assert.equal(data.assets[0].size, bytes.length);
    assert.equal(data.assets[0].digest, 'sha256:' + createHash('sha256').update(bytes).digest('hex'));
    assert.equal(data.assets[0].browser_download_url, 'https://github.com/NXN-MAX/OpenWRT-Athena/releases/download/v2.0.1/luci-theme-athena-2.0.1.tar.gz');
    assert.notEqual(run('2.0.1-rc1').status, 0);
    assert.notEqual(run('../../etc/passwd').status, 0);
    writeFileSync(join(dir, 'luci-theme-athena-2.0.1.tar.gz'), '');
    assert.notEqual(run('2.0.1').status, 0);
  } finally { rmSync(dir, {recursive: true, force: true}); }
});
