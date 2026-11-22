#!/bin/sh
# Only isolated temporary roots are modified; no live keys, feeds or packages.
set -eu
stage=$1
cd "$stage"
passed=0
ok() { passed=$((passed+1)); printf 'PASS %s\n' "$1"; }
reject() { label=$1; shift; if "$@" > reject.log 2>&1; then echo "FAIL accepted $label" >&2; exit 1; fi; ok "$label"; }
mkdir -p apk-keys wrong-keys extracted
cp public/keys/athena-apk.pub.pem apk-keys/athena.pub
cp wrong-apk.pub wrong-keys/wrong.pub
pkg=$(echo public/25.12/noarch/*.apk)
apk --keys-dir "$stage/apk-keys" verify "$pkg" >/dev/null
ok 'APK accepted by stock OpenWrt apk with Athena key'
apk --keys-dir "$stage/apk-keys" verify public/25.12/noarch/packages.adb >/dev/null
ok 'APK index accepted by stock OpenWrt apk'
reject 'APK rejected with another valid key' apk --keys-dir "$stage/wrong-keys" verify "$pkg"
cp "$pkg" altered.apk
printf 'BAD' | dd of=altered.apk bs=1 seek=16 conv=notrunc 2>/dev/null
reject 'altered APK rejected' apk --keys-dir "$stage/apk-keys" verify altered.apk
cp public/25.12/noarch/packages.adb altered.adb
printf 'BAD' | dd of=altered.adb bs=1 seek=16 conv=notrunc 2>/dev/null
reject 'altered APK index rejected' apk --keys-dir "$stage/apk-keys" verify altered.adb
usign -V -m public/24.10/all/Packages -p public/keys/athena-opkg.pub >/dev/null
ok 'opkg index signature verified by native usign'
usign -G -c test -s wrong-opkg.sec -p wrong-opkg.pub
reject 'opkg index rejected with another valid key' usign -V -m public/24.10/all/Packages -p wrong-opkg.pub
cp public/24.10/all/Packages altered-Packages
printf '\nchanged\n' >> altered-Packages
reject 'altered opkg index rejected' usign -V -m altered-Packages -x public/24.10/all/Packages.sig -p public/keys/athena-opkg.pub
(cd extracted && apk --keys-dir "$stage/apk-keys" extract "$stage/$pkg" >/dev/null)
test "$(wc -c < extracted/www/luci-static/athena/login.svg)" -eq 30280
ok 'signed APK extracts without executing installation scripts'
for version in 24.10.4 25.12.6; do
  root="$stage/root-$version"
  mkdir -p "$root/etc/opkg" "$root/etc/apk"
  printf "DISTRIB_RELEASE='%s'\n" "$version" > "$root/etc/openwrt_release"
  printf 'src/gz original https://example.invalid/official\n' > "$root/etc/opkg/customfeeds.conf"
  printf 'https://example.invalid/official.adb\n' > "$root/etc/apk/repositories"
  sh enable-feed.sh --root "$root" --key-dir "$stage/public/keys" > /dev/null
  sh enable-feed.sh --root "$root" --key-dir "$stage/public/keys" > /dev/null
  if [ "$version" = 24.10.4 ]; then
    test "$(grep -c '^src/gz athena ' "$root/etc/opkg/customfeeds.conf")" -eq 1
    grep -Fxq 'src/gz original https://example.invalid/official' "$root/etc/opkg/customfeeds.conf"
  else
    test "$(grep -c 'packages.adb$' "$root/etc/apk/repositories.d/athena.list")" -eq 1
    test "$(cat "$root/etc/apk/repositories")" = 'https://example.invalid/official.adb'
  fi
  ok "feed enable is idempotent and preserves original feeds on $version"
done
mkdir -p unsupported/etc
printf "DISTRIB_RELEASE='23.05.5'\n" > unsupported/etc/openwrt_release
reject 'unsupported firmware refused' sh enable-feed.sh --root "$stage/unsupported" --key-dir "$stage/public/keys"
mkdir -p bad-key-root/etc bad-public
printf "DISTRIB_RELEASE='25.12.6'\n" > bad-key-root/etc/openwrt_release
cp wrong-apk.pub bad-public/athena-apk.pub.pem
reject 'unrecognized public key refused before trust installation' sh enable-feed.sh --root "$stage/bad-key-root" --key-dir "$stage/bad-public"
test ! -d bad-key-root/etc/apk/keys
printf '%s native feed checks passed\n' "$passed"
