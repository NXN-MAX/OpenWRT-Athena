import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {transform} from 'lightningcss';

// Check authored CSS, excluding vendor code and the generated/minified asset.
// Complementary rules are valid; redeclaring a property for the same selector
// in the same media/supports context is where old patches silently accumulate.
export function checkStyles(css, filename = 'styles.css') {
  const seen = new Map(), errors = [];
  function walk(rules, context = []) {
    for (const rule of rules) {
      const value = rule.value;
      if (rule.type === 'style') {
        for (const selector of value.selectors) {
          const key = JSON.stringify([context, selector]);
          const previous = seen.get(key) || new Map();
          for (const declaration of [...value.declarations.declarations, ...value.declarations.importantDeclarations]) {
            const name = declaration.property === 'custom' ? declaration.value.name : declaration.property === 'unparsed' ? declaration.value.propertyId.property : declaration.property;
            const prefix = declaration.vendorPrefix || declaration.value?.propertyId?.vendorPrefix || declaration.value?.propertyId?.vendor_prefix;
            const property = name + (prefix ? ' ' + JSON.stringify(prefix) : '');
            const line = value.loc.line + 1;
            if (previous.has(property)) errors.push(`${filename}:${line}: repeated ${property} (first declared at line ${previous.get(property)})`);
            previous.set(property, line);
          }
          seen.set(key, previous);
        }
        walk(value.rules || [], [...context, JSON.stringify(value.selectors)]);
      } else if (value?.rules) {
        const {rules:children, loc, ...condition} = value;
        walk(children, [...context, JSON.stringify([rule.type, condition])]);
      }
    }
  }
  // source(none) is a Tailwind import extension, not standard CSS import syntax.
  const standardCSS=css.replace(/(@import\s+["']tailwindcss["'])\s+source\(none\)/g,'$1');
  transform({filename, code:Buffer.from(standardCSS), visitor:{StyleSheet(sheet) {walk(sheet.rules);}}});
  return errors;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const filename = 'src/styles.css';
  const errors = checkStyles(readFileSync(filename, 'utf8'), filename);
  if (errors.length) { console.error(errors.join('\n')); process.exitCode = 1; }
  else console.log('Authored CSS: no repeated selector properties or syntax errors.');
}
