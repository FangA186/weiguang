#!/bin/zsh
set -euo pipefail

ROOT=${0:A:h:h}
VERSION=0.5.6
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64)
    ASSET=deep-filter-0.5.6-aarch64-apple-darwin
    SHA256=4601e7f4e4c03e59a4c5b5000216ef3add3e808799cfccd95e14e83ea4611081
    ;;
  *)
    print -u2 "当前开发机架构尚未配置DeepFilterNet二进制：$(uname -s)-$(uname -m)"
    exit 1
    ;;
esac

mkdir -p "$ROOT/.tools"
TEMP=$(mktemp)
trap 'rm -f "$TEMP"' EXIT
curl -fL --retry 3 "https://github.com/Rikorose/DeepFilterNet/releases/download/v$VERSION/$ASSET" -o "$TEMP"
[[ $(shasum -a 256 "$TEMP" | awk '{print $1}') == $SHA256 ]] || { print -u2 "DeepFilterNet SHA-256校验失败"; exit 1; }
install -m 755 "$TEMP" "$ROOT/.tools/deep-filter"
"$ROOT/.tools/deep-filter" --version
