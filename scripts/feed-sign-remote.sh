#!/bin/sh
# Runs on a trusted signing host, never on a user's router during installation.
set -eu
umask 077
stage=$1
apk_tool=$2
cd "$stage"
test -s .private/opkg.sec && test -s .private/apk.pem
test -x "$apk_tool"
mkdir -p public/24.10/all public/25.12/noarch .verify-keys
cp public/keys/athena-apk.pub.pem .verify-keys/athena.pub
usign -S -m public/24.10/all/Packages -s .private/opkg.sec
usign -V -m public/24.10/all/Packages -p public/keys/athena-opkg.pub >&2
for file in public/25.12/noarch/*.apk; do
  # Only the maintainer's re-signing step accepts the SDK's original signature.
  "$apk_tool" adbsign --allow-untrusted --reset-signatures --sign-key .private/apk.pem "$file" >&2
  "$apk_tool" --keys-dir "$stage/.verify-keys" verify "$file" >&2
  "$apk_tool" adbdump --format json "$file" > public/package-info.json
done
"$apk_tool" mkndx --keys-dir "$stage/.verify-keys" --sign-key .private/apk.pem \
  --description 'Athena stable packages for OpenWrt 25.12' \
  --output public/25.12/noarch/packages.adb public/25.12/noarch/*.apk >&2
"$apk_tool" --keys-dir "$stage/.verify-keys" verify public/25.12/noarch/packages.adb >&2
usign -F -p public/keys/athena-opkg.pub > public/opkg-fingerprint.txt
# The output contains only public repository files, never .private or the helper.
tar -czf - -C public .
