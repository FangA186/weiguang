#!/bin/zsh
set -euo pipefail

ROOT_DIR=${0:A:h:h}
LOG_DIR="$ROOT_DIR/.run-logs"
mkdir -p "$LOG_DIR"

wait_for_url() {
  local name=$1
  local url=$2
  local log_file=$3
  local attempt
  for attempt in {1..40}; do
    if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
      print "✓ $name"
      return 0
    fi
    sleep 0.5
  done
  print -u2 "✗ $name 启动失败，查看：$log_file"
  return 1
}

submit_job() {
  local label=$1
  local log_file=$2
  local command=$3
  launchctl remove "$label" >/dev/null 2>&1 || true
  launchctl submit -l "$label" -o "$log_file" -e "$log_file" -- /bin/zsh -lc "$command"
}

if ! nc -z 127.0.0.1 55433 >/dev/null 2>&1; then
  if ! command -v docker >/dev/null 2>&1; then
    print -u2 "✗ PostgreSQL 未运行，且未找到 docker"
    exit 1
  fi
  print "→ 启动 PostgreSQL"
  docker compose -f "$ROOT_DIR/compose.postgres.yaml" up -d
else
  print "✓ PostgreSQL"
fi

if curl -fsS --max-time 2 http://127.0.0.1:8080/api/health >/dev/null 2>&1; then
  print "✓ FastAPI"
else
  if [[ ! -x "$ROOT_DIR/.venv/bin/python" ]]; then
    print -u2 "✗ 缺少 .venv，请先创建 Python 虚拟环境并安装 requirements.txt"
    exit 1
  fi
  print "→ 启动 FastAPI"
  submit_job com.weiguang.backend "$LOG_DIR/backend.log" \
    "export PATH='$ROOT_DIR/.tools':\$PATH; cd '$ROOT_DIR' && exec '$ROOT_DIR/.venv/bin/python' -m uvicorn backend.app:app --host 127.0.0.1 --port 8080 --reload"
  wait_for_url FastAPI http://127.0.0.1:8080/api/health "$LOG_DIR/backend.log"
fi

if curl -fsS --max-time 2 http://localhost:5173/ >/dev/null 2>&1; then
  print "✓ Vite (Consumer Frontend)"
else
  if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
    print -u2 "✗ 缺少 frontend/node_modules，请先在 frontend 执行 npm install"
    exit 1
  fi
  print "→ 启动 Vite (Consumer Frontend)"
  submit_job com.weiguang.frontend "$LOG_DIR/frontend.log" \
    "cd '$ROOT_DIR/frontend' && exec npm run dev -- --host 127.0.0.1 --port 5173"
  wait_for_url "Vite Frontend" http://localhost:5173/ "$LOG_DIR/frontend.log"
fi

if curl -fsS --max-time 2 http://localhost:5174/admin/ >/dev/null 2>&1; then
  print "✓ Vite (Admin Frontend)"
else
  if [[ ! -d "$ROOT_DIR/frontend-admin/node_modules" ]]; then
    print -u2 "✗ 缺少 frontend-admin/node_modules，请先在 frontend-admin 执行 npm install"
    exit 1
  fi
  print "→ 启动 Vite (Admin Frontend)"
  submit_job com.weiguang.frontend.admin "$LOG_DIR/frontend-admin.log" \
    "cd '$ROOT_DIR/frontend-admin' && exec npm run dev -- --host 127.0.0.1 --port 5174"
  wait_for_url "Vite Admin Frontend" http://localhost:5174/admin/ "$LOG_DIR/frontend-admin.log"
fi

print ""
print "微光已启动："
print "  用户端前端  http://localhost:5173"
print "  管理端前端  http://localhost:5174/admin/"
print "  后端服务    http://127.0.0.1:8080/api/health"
print "  运行日志    $LOG_DIR"
