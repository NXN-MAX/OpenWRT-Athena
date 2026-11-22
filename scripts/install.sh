#!/bin/sh
# Install a prebuilt Athena archive on an OpenWrt device.
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
command -v ucode >/dev/null
[ -f /usr/share/ucode/luci/dispatcher.uc ] || { echo 'A ucode-based LuCI installation is required' >&2; exit 1; }
[ -s "$BASE/htdocs/luci-static/athena/athena.css" ]
for file in "$BASE"/ucode/template/themes/athena/*.ut; do ucode -T -c -o /dev/null "$file"; done
ucode -c -o /dev/null "$BASE/root/usr/share/rpcd/ucode/luci.athena"
cp -R "$BASE/htdocs/." /www/
cp -R "$BASE/ucode/." /usr/share/ucode/luci/
cp -R "$BASE/root/usr/." /usr/
chmod 0755 /usr/libexec/athena-update
[ -f /etc/config/athena ] || cp "$BASE/root/etc/config/athena" /etc/config/athena
sh "$BASE/root/etc/uci-defaults/30_luci-theme-athena"
/etc/init.d/rpcd reload
/etc/init.d/uhttpd reload
printf 'Athena installed. Reload LuCI.\n'
