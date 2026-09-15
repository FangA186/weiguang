#!/bin/zsh
set -euo pipefail

ROOT=${0:A:h:h}
SOURCE_ENV=${1:-$ROOT/.env}
OUTPUT=${2:-$ROOT/release/weiguang-production.tar.gz}
[[ -f $SOURCE_ENV ]] || { print -u2 "Missing source environment: $SOURCE_ENV"; exit 1; }

STAGE=$(mktemp -d)
mkdir -p "$STAGE/weiguang/marketing_assets/2026-08-24" "$STAGE/weiguang/marketing_assets/2026-09-08/holo-card-experiment" "${OUTPUT:h}"
cp "$ROOT/Dockerfile" "$ROOT/.dockerignore" "$ROOT/requirements.txt" "$STAGE/weiguang/"
cp -R "$ROOT/backend" "$ROOT/internal" "$ROOT/deploy" "$STAGE/weiguang/"
tar -C "$ROOT" --exclude='frontend/node_modules' --exclude='frontend/dist' -cf - frontend | tar -C "$STAGE/weiguang" -xf -
cp "$ROOT/marketing_assets/2026-08-24/04-lifestyle-v2.png" "$STAGE/weiguang/marketing_assets/2026-08-24/"
cp "$ROOT/marketing_assets/2026-09-08/holo-card-experiment/weiguang-subject-transparent.png" "$STAGE/weiguang/marketing_assets/2026-09-08/holo-card-experiment/"

DB_PASSWORD=$(openssl rand -hex 24)
umask 077
{
  print 'APP_ENV=staging'
  print 'COOKIE_SECURE=false'
  print 'PUBLIC_BASE_URL=http://47.114.50.170'
  print 'TRUSTED_ORIGINS=http://47.114.50.170'
  print 'POSTGRES_DB=weiguang'
  print 'POSTGRES_USER=weiguang'
  print "POSTGRES_PASSWORD=$DB_PASSWORD"
  print "DATABASE_URL=postgresql://weiguang:$DB_PASSWORD@postgres:5432/weiguang"
  awk '/^(QWEN_API_KEY|DASHSCOPE_API_KEY|QWEN_BASE_URL|QWEN_LLM_MODEL|QWEN_TTS_MODEL|QWEN_TTS_FALLBACK_MODEL|QWEN_TTS_VOICE|BAILIAN_TTS_URL|BAILIAN_VOICE_CLONE_URL|OSS_REGION|OSS_BUCKET|OSS_PUBLIC_ENDPOINT|OSS_INTERNAL_ENDPOINT|OSS_ACCESS_KEY|OSS_SECRET_KEY|MAX_UPLOAD_MB|MAX_AUDIO_SECONDS|MAX_CONCURRENT_TURNS|FREE_REQUEST_QUOTA|BILLING_ENFORCEMENT_MODE|BILLING_HARD_USER_IDS|LDXP_PLUS_PRODUCT_URL|LDXP_PRO_PRODUCT_URL|MONITOR_DAILY_BUDGET_CNY|MONITOR_FAILURE_RATE_PERCENT|QWEN_LLM_INPUT_CNY_PER_MILLION|QWEN_LLM_OUTPUT_CNY_PER_MILLION|QWEN_TTS_CNY_PER_10K_CHARACTERS)=/' "$SOURCE_ENV"
} > "$STAGE/weiguang/.env.production"

for required in DASHSCOPE_API_KEY QWEN_BASE_URL OSS_BUCKET OSS_ACCESS_KEY OSS_SECRET_KEY; do
  grep -Eq "^${required}=.+" "$STAGE/weiguang/.env.production" || { print -u2 "Missing production value: $required"; exit 1; }
done
tar -C "$STAGE" -czf "$OUTPUT" weiguang
chmod 600 "$OUTPUT"
print "$OUTPUT"
