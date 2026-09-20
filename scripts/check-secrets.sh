#!/usr/bin/env bash
# Fail on live secret material in tracked files. Placeholders stay allowed.
# Usage: ./scripts/check-secrets.sh [path]
set -euo pipefail
ROOT="${1:-pulsedesk-os}"
PATTERN='apikey_[A-Za-z0-9_-]{8,}|AQ\.Ab8[A-Za-z0-9_-]{8,}|sk-(live|test)[A-Za-z0-9]{8,}|xox[bap]-[A-Za-z0-9-]{8,}'
if grep -rnE "$PATTERN" "$ROOT" --include='*.py' --include='*.md' --include='*.json' \
  --include='*.yaml' --include='*.yml' --include='*.tsx' --include='*.ts' \
  --include='*.sh' --include='*.toml' 2>/dev/null | grep -v node_modules | grep -v '/dist/'; then
  echo "SECRETS-CHECK: FAIL — live secret material above"
  exit 1
fi
echo "SECRETS-CHECK: PASS"
