#!/bin/zsh
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_FILE:?BACKUP_FILE is required}"
if [[ "${CONFIRM_RESTORE:-}" != "YES" ]]; then
  print -u2 "refusing restore: set CONFIRM_RESTORE=YES after verifying BACKUP_FILE and DATABASE_URL"
  exit 2
fi
[[ -f "$BACKUP_FILE" ]] || { print -u2 "backup file not found"; exit 2; }
pg_restore --clean --if-exists --exit-on-error --dbname="$DATABASE_URL" "$BACKUP_FILE"
print "database restored from $BACKUP_FILE"
