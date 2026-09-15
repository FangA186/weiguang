#!/usr/bin/env bash
set -Eeuo pipefail

payload_dir=${1:-$(cd "$(dirname "$0")" && pwd)}
app_dir=/opt/weiguang
admin_root=/var/www/weiguang-admin
nginx_conf=/etc/nginx/default.d/weiguang.conf
env_file=$app_dir/.env.production
compose_file=$app_dir/deploy/compose.production.yaml
release_id=$(<"$payload_dir/RELEASE_ID")
backup_dir=$app_dir/releases/backup-$release_id
rollback_image=deploy-api:rollback-$release_id
published=0

[[ $EUID -eq 0 ]] || { echo "请使用 root 或 sudo 执行" >&2; exit 1; }
for command in docker nginx curl gzip; do command -v "$command" >/dev/null || { echo "缺少命令：$command" >&2; exit 1; }; done
[[ -f $env_file ]] || { echo "缺少生产配置：$env_file" >&2; exit 1; }
[[ -f $payload_dir/deploy-api.tar.gz && -d $payload_dir/admin ]] || { echo "发布包不完整" >&2; exit 1; }

mkdir -p "$backup_dir" "$app_dir/deploy" "$admin_root"
[[ -f $compose_file ]] && cp "$compose_file" "$backup_dir/compose.production.yaml"
[[ -f $nginx_conf ]] && cp "$nginx_conf" "$backup_dir/weiguang.conf"
[[ -d $admin_root/admin ]] && mv "$admin_root/admin" "$backup_dir/admin"

current_image=$(docker image inspect deploy-api:latest --format '{{.Id}}' 2>/dev/null || true)
[[ -n $current_image ]] && docker tag "$current_image" "$rollback_image"

rollback() {
  local rc=$?
  if (( rc != 0 && published == 0 )); then
    echo "发布失败，恢复上一版本" >&2
    [[ -f $backup_dir/compose.production.yaml ]] && cp "$backup_dir/compose.production.yaml" "$compose_file"
    [[ -f $backup_dir/weiguang.conf ]] && cp "$backup_dir/weiguang.conf" "$nginx_conf"
    rm -rf "$admin_root/admin"
    [[ -d $backup_dir/admin ]] && mv "$backup_dir/admin" "$admin_root/admin"
    if docker image inspect "$rollback_image" >/dev/null 2>&1; then
      docker tag "$rollback_image" deploy-api:latest
      docker compose --env-file "$env_file" -f "$compose_file" up -d --no-deps --force-recreate --no-build api || true
    fi
    nginx -t >/dev/null 2>&1 && systemctl reload nginx || true
  fi
  exit "$rc"
}
trap rollback EXIT

postgres_id=$(docker compose --env-file "$env_file" -f "$compose_file" ps -q postgres)
[[ -n $postgres_id ]] || { echo "PostgreSQL 容器未运行" >&2; exit 1; }
docker exec "$postgres_id" sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$backup_dir/database.dump"

gzip -dc "$payload_dir/deploy-api.tar.gz" | docker load >/dev/null
cp "$payload_dir/compose.production.yaml" "$compose_file"
cp "$payload_dir/nginx-default-location.conf" "$nginx_conf"
cp -R "$payload_dir/admin" "$admin_root/admin"
chmod -R a+rX "$admin_root/admin"
nginx -t
systemctl reload nginx

docker compose --env-file "$env_file" -f "$compose_file" up -d --no-deps --force-recreate --no-build api
for _ in {1..30}; do
  curl -fsS http://127.0.0.1/api/health >/dev/null && break
  sleep 1
done
curl -fsS http://127.0.0.1/api/health >/dev/null
curl -fsS http://127.0.0.1/ >/dev/null
curl -fsS http://127.0.0.1/admin/ | grep -q '微光运营管理后台'

published=1
trap - EXIT
echo "发布成功：$release_id"
echo "数据库备份：$backup_dir/database.dump"
