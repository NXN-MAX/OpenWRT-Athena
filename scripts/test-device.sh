#!/bin/sh
set -eu
BASE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ATHENA_SSH_CMD=${ATHENA_SSH:-"$BASE/../scripts/ssh.sh"}
sed 's@/www/luci-static/athena/branding@/tmp/athena-rpc-test-assets@' "$BASE/root/usr/share/rpcd/ucode/luci.athena" | "$ATHENA_SSH_CMD" 'cat > /tmp/athena-rpc-test.uc'
cat "$BASE/tests/fixtures/icon.png" | "$ATHENA_SSH_CMD" 'cat > /tmp/athena-test-icon.png'
cat "$BASE/tests/rpc.uc" | "$ATHENA_SSH_CMD" 'cat > /tmp/athena-tests.uc; ucode /tmp/athena-tests.uc'
"$ATHENA_SSH_CMD" 'rm -rf /tmp/athena-rpc-test-assets /tmp/athena-rpc-test.uc /tmp/athena-test-icon.png /tmp/athena-tests.uc'
