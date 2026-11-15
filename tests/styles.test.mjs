import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {checkStyles} from '../scripts/check-styles.mjs';

test('authored styles pass the duplicate-property and syntax gate',()=>{
  assert.deepEqual(checkStyles(readFileSync(new URL('../src/styles.css',import.meta.url),'utf8')),[]);
});
test('style gate catches old overrides even in repeated equivalent media queries',()=>{
  const errors=checkStyles('.topbar{background:red}.topbar{background:blue}@media(max-width:767px){.panel{padding:4px}}@media (max-width: 767px){.panel{padding:8px}}');
  assert.equal(errors.length,2);assert.match(errors[0],/background/);assert.match(errors[1],/padding/);
});
test('style gate permits responsive variants, complementary rules and vendor fallbacks',()=>{
  assert.deepEqual(checkStyles('.panel{padding:8px}.panel{color:red}@media(max-width:767px){.panel{padding:4px}}.glass{-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px)}'),[]);
});
test('style gate accepts explicit Tailwind source scope while still checking authored rules',()=>{
  const errors=checkStyles('@import "tailwindcss" source(none);.panel{color:red}.panel{color:blue}');
  assert.equal(errors.length,1);assert.match(errors[0],/color/);
});
test('style gate distinguishes variable filter vendor prefixes and still catches each repeated fallback',()=>{
  const filters='.glass{-webkit-backdrop-filter:blur(var(--blur,20px));backdrop-filter:blur(var(--blur,20px))}';
  assert.deepEqual(checkStyles(filters),[]);
  const errors=checkStyles(filters+filters);
  assert.equal(errors.length,2);assert(errors.every(error=>error.includes('backdrop-filter')));
});
