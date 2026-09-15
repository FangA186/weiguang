#!/bin/zsh
set -euo pipefail

ROOT=${0:A:h:h}
RELEASE_ID=${RELEASE_ID:-$(date -u +%Y%m%dT%H%M%SZ)}
OUTPUT=${OUTPUT:-$ROOT/release/weiguang-$RELEASE_ID.tar.gz}
DEPLOY_TARGET=${DEPLOY_TARGET:-}
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

for command in docker npm node tar gzip shasum; do
  command -v "$command" >/dev/null || { print -u2 "缺少命令：$command"; exit 1; }
done
docker info >/dev/null 2>&1 || { print -u2 "Docker Desktop 未运行"; exit 1; }

print "→ 检查并构建用户端"
(cd "$ROOT/frontend" && node --test tests/mobileA11y.test.mjs && npm run type-check && npm run build)
print "→ 检查并构建管理端"
(cd "$ROOT/frontend-admin" && npm test && npm run type-check && npm run build)
[[ -x $ROOT/.venv/bin/python ]] && "$ROOT/.venv/bin/python" -m compileall -q "$ROOT/backend"

print "→ 构建 linux/amd64 API 镜像"
docker buildx build --platform linux/amd64 --load -t deploy-api:latest -f "$ROOT/deploy/Dockerfile.prebuilt" "$ROOT"
[[ $(docker image inspect deploy-api:latest --format '{{.Architecture}}') == amd64 ]] || { print -u2 "API 镜像不是 amd64"; exit 1; }

PAYLOAD=$STAGE/weiguang-release
mkdir -p "$PAYLOAD/admin" "${OUTPUT:h}"
print -r -- "$RELEASE_ID" > "$PAYLOAD/RELEASE_ID"
docker image save deploy-api:latest | gzip -1 > "$PAYLOAD/deploy-api.tar.gz"
cp -R "$ROOT/frontend-admin/dist/." "$PAYLOAD/admin/"
cp "$ROOT/deploy/compose.production.yaml" "$PAYLOAD/"
cp "$ROOT/deploy/nginx-default-location.conf" "$PAYLOAD/"
cp "$ROOT/deploy/apply-release.sh" "$PAYLOAD/"
chmod +x "$PAYLOAD/apply-release.sh"
tar -C "$STAGE" -czf "$OUTPUT" weiguang-release
chmod 600 "$OUTPUT"
shasum -a 256 "$OUTPUT" > "$OUTPUT.sha256"

print "✓ 发布包：$OUTPUT"
print "✓ 校验文件：$OUTPUT.sha256"

if [[ -z $DEPLOY_TARGET ]]; then
  print "未设置 DEPLOY_TARGET，仅生成发布包。"
  print "配置 SSH 后执行：DEPLOY_TARGET=root@47.114.50.170 $0"
  exit 0
fi

for command in ssh scp; do command -v "$command" >/dev/null || { print -u2 "缺少命令：$command"; exit 1; }; done
ssh -o BatchMode=yes "$DEPLOY_TARGET" true || { print -u2 "SSH 密钥登录不可用：$DEPLOY_TARGET"; exit 1; }
remote_archive=/tmp/${OUTPUT:t}
scp "$OUTPUT" "$DEPLOY_TARGET:$remote_archive"
ssh "$DEPLOY_TARGET" "set -e; d=\$(mktemp -d /tmp/weiguang-release.XXXXXX); tar -xzf '$remote_archive' -C \"\$d\"; if [ \$(id -u) -eq 0 ]; then \"\$d/weiguang-release/apply-release.sh\" \"\$d/weiguang-release\"; else sudo \"\$d/weiguang-release/apply-release.sh\" \"\$d/weiguang-release\"; fi; rm -rf \"\$d\" '$remote_archive'"
print "✓ 线上发布完成：http://47.114.50.170/"
