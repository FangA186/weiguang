#!/bin/zsh
set -euo pipefail
umask 077

: "${DATABASE_URL:?DATABASE_URL is required}"
backup_dir=${BACKUP_DIR:-./backups}
mkdir -p "$backup_dir"
backup_file="$backup_dir/weiguang-$(date -u +%Y%m%dT%H%M%SZ).dump"
pg_dump --format=custom --file="$backup_file" "$DATABASE_URL"
print "database backup written to $backup_file"
