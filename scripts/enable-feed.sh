#!/bin/sh
# Explicitly enable the third-party Athena feed; never disables signature checking.
set -eu
umask 022
root=/
key_dir=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --root) root=$2; shift 2 ;;
    --key-dir) key_dir=$2; shift 2 ;;
    *) echo 'Usage: enable-feed.sh [--root /offline/root] [--key-dir /verified/public/keys]' >&2; exit 2 ;;
  esac
done
case "$root" in /*) ;; *) echo 'Root must be absolute' >&2; exit 2 ;; esac
prefix=$(cd "$root" && pwd -P)
[ "$prefix" != / ] || prefix=
release=$(grep '^DISTRIB_RELEASE=' "$prefix/etc/openwrt_release" | cut -d= -f2- | tr -d "\"'")
base='https://raw.githubusercontent.com/NXN-MAX/OpenWRT-Athena/feeds'
case "$release" in
  24.10|24.10.*) manager=opkg; key=athena-opkg.pub; key_hash=f54629556f98e848b5e8b04ad7b53c730bed33ce22da7591c70d24bcc1f178da
    key_target="$prefix/etc/opkg/keys/efe004bab7c083b3"
    repo_target="$prefix/etc/opkg/customfeeds.conf"
    repo_line="src/gz athena $base/24.10/all" ;;
  25.12|25.12.*) manager=apk; key=athena-apk.pub.pem; key_hash=6fc101f3c59dd1a98a1f3e172eb768f79e1298d1e09b9ec0bd34874b8aee3420
    key_target="$prefix/etc/apk/keys/athena.pub.pem"
    repo_target="$prefix/etc/apk/repositories.d/athena.list"
    repo_line="$base/25.12/noarch/packages.adb" ;;
  *) echo "Unsupported OpenWrt release: $release (only 24.10 and 25.12 are published)" >&2; exit 1 ;;
esac
work=$(mktemp -d /tmp/athena-feed-enable.XXXXXX)
trap 'rm -rf "$work"' EXIT HUP INT TERM
if [ -n "$key_dir" ]; then
  [ -f "$key_dir/$key" ] && [ ! -L "$key_dir/$key" ]
  cp "$key_dir/$key" "$work/key"
else
  command -v curl >/dev/null
  curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
    --connect-timeout 5 --max-time 30 --max-filesize 8192 \
    "https://raw.githubusercontent.com/NXN-MAX/OpenWRT-Athena/main/keys/$key" -o "$work/key"
fi
printf '%s  %s\n' "$key_hash" "$work/key" | sha256sum -c - >/dev/null
if [ -e "$key_target" ] || [ -L "$key_target" ]; then
  [ -f "$key_target" ] && [ ! -L "$key_target" ] && cmp -s "$work/key" "$key_target" || {
    echo 'Existing Athena key differs; refusing automatic key replacement' >&2; exit 1;
  }
fi
if [ -e "$repo_target" ] || [ -L "$repo_target" ]; then
  [ -f "$repo_target" ] && [ ! -L "$repo_target" ] || { echo 'Invalid feed configuration path' >&2; exit 1; }
  if [ "$manager" = apk ]; then
    grep -Fxq "$repo_line" "$repo_target" || { echo 'Existing athena.list differs; review it before enabling this feed' >&2; exit 1; }
  elif grep -Eq '^[[:space:]]*src(/gz)?[[:space:]]+athena[[:space:]]' "$repo_target"; then
    grep -Fxq "$repo_line" "$repo_target" || { echo 'Existing athena feed differs; review it before enabling this feed' >&2; exit 1; }
  fi
fi
mkdir -p "$(dirname "$key_target")" "$(dirname "$repo_target")"
if [ ! -f "$key_target" ]; then
  cp "$work/key" "$key_target.athena-next"; chmod 0644 "$key_target.athena-next"; mv "$key_target.athena-next" "$key_target"
fi
if ! grep -Fxq "$repo_line" "$repo_target" 2>/dev/null; then
  [ ! -f "$repo_target" ] || cp -p "$repo_target" "$repo_target.athena-backup"
  { if [ -f "$repo_target" ]; then cat "$repo_target"; printf '\n'; fi; printf '%s\n' "$repo_line"; } > "$repo_target.athena-next"
  chmod 0644 "$repo_target.athena-next"; mv "$repo_target.athena-next" "$repo_target"
fi
echo "Athena $manager feed enabled; official firmware feeds were preserved."
echo "Public-key file SHA256: $key_hash"
if [ "$manager" = apk ]; then
  printf 'Next: apk update\n      apk add luci-theme-athena\n'
else
  printf 'Next: opkg update\n      opkg install luci-theme-athena\n'
fi
