#!/usr/bin/env python3
"""Create a reviewable LuCI upstream edition in a new, empty package directory.

Does not commit, sign off, push, install, or modify the independent edition.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil

BASE = Path(__file__).resolve().parent.parent
LITERAL = r'''(?:'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")'''
PAIR = re.compile(r'\b(?:t|text)\(\s*(' + LITERAL + r')\s*,\s*(' + LITERAL + r')\s*\)')


def upstream(destination):
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Destination must be a new or empty directory')
    destination.mkdir(parents=True, exist_ok=True)
    for name in ['htdocs', 'ucode', 'root', 'licenses']:
        shutil.copytree(BASE / name, destination / name)
    # luci.mk treats any src/ directory as native compiled installation input.
    shutil.copytree(BASE / 'src', destination / 'style-src')
    for name in ['LICENSE', 'NOTICE', 'package-lock.json']:
        shutil.copy2(BASE / name, destination / name)
    (destination / 'root/usr/libexec/athena-update').unlink()
    for path in sorted((destination / 'root/usr/libexec').rglob('*'), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    if not any((destination / 'root/usr/libexec').iterdir()):
        (destination / 'root/usr/libexec').rmdir()
    version = json.loads((BASE / 'package.json').read_text())['version']
    (destination / 'Makefile').write_text('''# SPDX-License-Identifier: Apache-2.0
include $(TOPDIR)/rules.mk

LUCI_TITLE:=Athena theme
LUCI_PKGARCH:=all
LUCI_MAINTAINER:=ZHICHENG CHEN <czhic1996@gmail.com>
LUCI_DEPENDS:=+luci-base +rpcd-mod-ucode +ucode-mod-fs +ucode-mod-uci
PKG_VERSION:=''' + version + '''
PKG_RELEASE:=1
PKG_LICENSE:=Apache-2.0 AND MIT
PKG_LICENSE_FILES:=LICENSE licenses/gravity-ui-icons-MIT.txt

# Prebuilt modern CSS and source templates are shipped in the repository.
# Legacy csstidy cannot preserve CSS layers, color-mix() and nesting.
LUCI_MINIFY_CSS:=0
LUCI_MINIFY_UT:=0

define Package/luci-theme-athena/conffiles
/etc/config/athena
endef

define Package/luci-theme-athena/postrm
#!/bin/sh
[ -n "$${IPKG_INSTROOT}" ] || {
\tuci -q delete luci.themes.Athena
\tuci commit luci
}
endef

include ../../luci.mk

# call BuildPackage - OpenWrt buildroot signature
''')
    # Registration must not replace the administrator's selected theme.
    (destination / 'root/etc/uci-defaults/30_luci-theme-athena').write_text('''#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
uci -q get luci.themes >/dev/null || uci set luci.themes=internal
uci set luci.themes.Athena='/luci-static/athena'
uci commit luci
exit 0
''')
    rpc = destination / 'root/usr/share/rpcd/ucode/luci.athena'
    source = rpc.read_text().replace('// Athena assets and GitHub releases, native rpcd ucode.', '// SPDX-License-Identifier: Apache-2.0\n// Athena asset management, native rpcd ucode.')
    source = source.replace(', rmdir }', ' }').replace("const updateRoot = '/var/run/athena-update';\n", '')
    source = source[:source.index('function newer(')] + source[source.index('function u32('):]
    source = re.sub(r'^  (check_update|update_status|start_update):.*\n', '', source, flags=re.M)
    rpc.write_text(source)
    acl = destination / 'root/usr/share/rpcd/acl.d/luci-theme-athena.json'
    value = json.loads(acl.read_text())
    scope = value['luci-theme-athena']
    scope['description'] = 'Configure Athena appearance and manage login assets'
    scope['read']['ubus']['luci.athena'] = ['get']
    scope['write']['ubus']['luci.athena'] = ['install', 'select', 'remove']
    acl.write_text(json.dumps(value, indent=2) + '\n')
    menu = destination / 'root/usr/share/luci/menu.d/luci-theme-athena.json'
    value = json.loads(menu.read_text())
    value['admin/system/Athena-config']['title'] = 'Athena theme'
    menu.write_text(json.dumps(value, indent=2) + '\n')
    view = destination / 'htdocs/luci-static/resources/view/athena-config.js'
    source = view.read_text()
    source = re.sub(r'^const (checkUpgrade|startUpgrade|upgradeStatus)=.*\n', '', source, flags=re.M)
    source = source[:source.index('function upgradeError(')] + source[source.index('return view.extend'):]
    source = re.sub(r'^  upgradeStatus\(.*\n', '', source, flags=re.M)
    source = source.replace("t('管理主题外观、登录页素材与版本更新。','Appearance, login assets and theme updates.')", "_('Manage appearance and login assets.')")
    source = source.replace("Promise.all([uci.load('athena'),callGet()])", "Promise.all([uci.load('athena'),callGet(),ui.menu.load().catch(()=>null)])")
    source = source.replace("this.readonly=!L.hasViewPermission();this.assets=checked(data[1]);", "this.readonly=!L.hasViewPermission();this.assets=checked(data[1]);\n  const system=data[2]?.children?.admin?.children?.system?.children;\n  this.packagePath=['package-manager','opkg','apk'].find(name=>system?.[name]?.satisfied!==false&&system?.[name]?.title);")
    start = source.index(' renderUpgrade:function(){')
    stop = source.index(' update:function(result)', start)
    source = source[:start] + ''' renderUpgrade:function(){
  this.upgradeRoot.replaceChildren(widgets.card(E('h3',{},_('Theme version')),[
   E('p',{},_('Current version')+': v'+this.assets.version),
   E('p',{},_('Install and update this theme through the OpenWrt package manager.')),
   this.packagePath?E('a',{class:'button button--secondary button--sm',href:L.url('admin','system',this.packagePath)},_('Software')):''
  ]));
 },
''' + source[stop:]
    view.write_text(source)
    catalog = {}
    def gettext_pair(match):
        chinese, english = (ast.literal_eval(match[index]) for index in [1, 2])
        prefix = english[:len(english) - len(english.lstrip())]
        suffix = english[len(english.rstrip()):]
        if prefix:
            chinese = chinese.lstrip()
        if suffix:
            chinese = chinese.rstrip()
        catalog[english.strip()] = chinese
        parts = ([json.dumps(prefix)] if prefix else []) + ['_(' + json.dumps(english.strip()) + ')'] + ([json.dumps(suffix)] if suffix else [])
        return ' + '.join(parts)
    for file in destination.rglob('*.js'):
        source = file.read_text()
        source = PAIR.sub(gettext_pair, source)
        source = re.sub(r'^const (?:t|text)\s*=.*\n', '', source, flags=re.M)
        source = re.sub(r'^const zh\s*=.*\n', '', source, flags=re.M)
        source = source.replace("toLocaleTimeString(zh?'zh-CN':'en',", 'toLocaleTimeString(document.documentElement.lang,')
        if re.search(r'\b(?:t|text)\(', source):
            raise ValueError('Unconverted translation helper: ' + str(file))
        file.write_text(source)
    header = destination / 'ucode/template/themes/athena/header.ut'
    source = header.read_text().replace("const mode_labels = substr(dispatcher.lang, 0, 2) == 'zh' ? { light: '日光模式', dark: '暗黑模式', system: '跟随系统' } : { light: 'Light mode', dark: 'Dark mode', system: 'Follow system' };", "const mode_labels = { light: _('Light mode'), dark: _('Dark mode'), system: _('Follow system') };")
    source = source.replace("substr(dispatcher.lang, 0, 2) == 'zh' ? '外观模式' : 'Appearance'", "_('Appearance')")
    header.write_text(source)
    auth = destination / 'ucode/template/themes/athena/sysauth.ut'
    source = auth.read_text()
    source = source.replace("substr(dispatcher.lang, 0, 2) == 'zh' ? '显示密码' : _('Show password')", "_('Show password')")
    source = source.replace("substr(dispatcher.lang, 0, 2) == 'zh' ? '隐藏密码' : _('Hide password')", "_('Hide password')")
    auth.write_text(source)
    # Development tooling is optional. SDK builds consume the checked-in CSS.
    package = json.loads((BASE / 'package.json').read_text())
    package['scripts'] = {
        'build': 'node scripts/build.mjs',
        'test': 'node --test tests/*.test.mjs',
    }
    (destination / 'package.json').write_text(json.dumps(package, indent=2) + '\n')
    (destination / 'scripts').mkdir()
    (destination / 'scripts/build.mjs').write_text("""import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
const result = spawnSync('node_modules/.bin/tailwindcss', ['-i', 'style-src/styles.css', '-o', 'htdocs/luci-static/athena/athena.css', '--minify'], { stdio: 'inherit' });
if (result.status !== 0) process.exit(result.status || 1);
const walk = path => readdirSync(path, { withFileTypes: true }).sort((a,b) => a.name.localeCompare(b.name)).flatMap(entry => entry.isDirectory() ? walk(join(path, entry.name)) : [join(path, entry.name)]);
const digest = createHash('sha256');
for (const path of walk('htdocs').filter(path => !path.endsWith('/version'))) digest.update(readFileSync(path));
writeFileSync('htdocs/luci-static/athena/version', digest.digest('hex').slice(0,12));
""")
    (destination / 'tests/fixtures').mkdir(parents=True)
    for name in ['native-dom.test.mjs', 'summary.test.mjs', 'theme.test.mjs', 'rpc.uc', 'fixtures/icon.png']:
        shutil.copy2(BASE / 'tests' / name, destination / 'tests' / name)
    (destination / 'tests/translations.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    # Existing DOM regressions use a Chinese fixture, now backed by a gettext stub.
    test_file = destination / 'tests/native-dom.test.mjs'
    source = test_file.read_text().replace("const source=readFileSync", "const translations=JSON.parse(readFileSync(new URL('./translations.json',import.meta.url),'utf8'));\nconst source=readFileSync", 1)
    source = source.replace('E,s=>s,class', "E,s=>lang.startsWith('zh')?(translations[s]||s):s,class")
    test_file.write_text(source)
    test_file = destination / 'tests/summary.test.mjs'
    source = test_file.read_text().replace("const source=readFileSync", "const translations=JSON.parse(readFileSync(new URL('./translations.json',import.meta.url),'utf8'));\nconst source=readFileSync", 1)
    source = source.replace("'cancelAnimationFrame',source)", "'cancelAnimationFrame','_',source)")
    source = source.replace('id=>frames.delete(id));', 'id=>frames.delete(id),s=>translations[s]||s);')
    test_file.write_text(source)
    shutil.copy2(BASE / 'tests/upstream/settings.mjs', destination / 'tests/settings.test.mjs')
    shutil.copy2(BASE / 'scripts/test-device.sh', destination / 'scripts/test-device.sh')
    (destination / 'README.md').write_text('''# Athena LuCI theme

A native ucode/JavaScript theme using HeroUI's framework-independent CSS.
There is no React, Lua compatibility layer, external update service, package
feed configuration or bundled private key. Installation registers Athena under
System → System → Language and Style without changing the selected theme.

The theme includes light, dark and system appearance, responsive navigation,
native LuCI form/table adapters, status summaries, and optional local login
assets. The asset RPC has scoped ACLs and validates paths, formats and sizes.
Normal LuCI UCI save/apply and application polling remain in place. Uninstalling
the package removes only its theme registration; local settings are retained.

## Build and development

The standard LuCI `luci.mk` builds this package from checked-in CSS, JavaScript,
templates and RPC sources. SDK builds and routers do not require Node.js.
Source templates are shipped to avoid binding packages to host ucode bytecode.
Modern CSS is already minified; legacy csstidy is disabled for this package only.

To regenerate CSS on a development host, use the pinned package-lock.json:

```sh
npm ci
npm run build
npm test
```

Strings use LuCI gettext. Generate the initial catalog with
`./build/i18n-scan.pl themes/luci-theme-athena` at the LuCI repository root;
translations should be contributed through OpenWrt Weblate.

Test browser requirement: modern CSS with :has(), color-mix(), and mask support.
The popover and theme-transition integrations have progressive fallbacks;
reduced-motion preferences are respected. See NOTICE and licenses/ for
Bootstrap, HeroUI and Gravity Icons attribution. Apache-2.0 and MIT apply.
''')
    (destination / '.gitignore').write_text('node_modules/\n')
    digest = hashlib.sha256()
    for file in sorted((destination / 'htdocs').rglob('*')):
        if file.is_file() and file.name != 'version':
            digest.update(file.read_bytes())
    (destination / 'htdocs/luci-static/athena/version').write_text(digest.hexdigest()[:12])
    print('Prepared upstream edition: ' + str(destination))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    upstream(parser.parse_args().destination.resolve())
