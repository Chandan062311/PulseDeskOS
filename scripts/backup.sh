#!/usr/bin/env bash
# Online SQLite backup via the backup API (safe under write load).
# Usage: MEMORY_DB=/data/memory.db ./scripts/backup.sh [/backup/dir]
set -euo pipefail
DB="${MEMORY_DB:-memory.db}"
OUT_DIR="${1:-./backups}"
mkdir -p "$OUT_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$OUT_DIR/memory-$STAMP.db"
python3 - "$DB" "$OUT" << 'PY'
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
with sqlite3.connect(src) as s, sqlite3.connect(dst) as d:
    s.backup(d)
print(dst)
PY
