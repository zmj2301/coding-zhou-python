#!/usr/bin/env bash
# 湘潭实时公交 v1.0.0 —— APK 构建脚本
#
# 前置条件（Windows，需管理员 + 一次重启）：
#   wsl --install -d Ubuntu-22.04
#
# 用法：
#   bash build_apk.sh          # 构建 debug APK
#
set -e
cd "$(dirname "$0")"

VERSION="1.1.0"
echo "=============================================="
echo " 湘潭实时公交 v${VERSION}  APK 构建"
echo "=============================================="

command -v wsl >/dev/null 2>&1 || { echo "✗ 未检测到 WSL"; exit 1; }

echo "[1/4] 同步源码到 WSL ..."
WSL_DIR="$HOME/xiangtanbus"
wsl -d Ubuntu-22.04 -- bash -c "mkdir -p $WSL_DIR"

# 只同步必要文件
wsl -d Ubuntu-22.04 -- bash -c "rm -rf $WSL_DIR/* " || true
wsl -d Ubuntu-22.04 -- bash -c "mkdir -p $WSL_DIR/busapp"
for f in app_main.py cli.py buildozer.spec icon.png presplash.png; do
  wsl -d Ubuntu-22.04 -- bash -c "cp '$(wslpath -w "$(pwd)/$f" 2>/dev/null || echo "/mnt/c/$(pwd | sed 's|C:|c|')/$f")' $WSL_DIR/" || true
done
wsl -d Ubuntu-22.04 -- bash -c "cp /mnt/$(pwd | sed 's|^\([A-Za-z]\):|\l\1|')/busapp/*.py $WSL_DIR/busapp/"

echo "[2/4] 安装 buildozer ..."
wsl -d Ubuntu-22.04 -- bash -lc "python3 -m pip install --user --upgrade buildozer cython" || {
  wsl -d Ubuntu-22.04 -- bash -lc "sudo apt-get update && sudo apt-get install -y python3-pip python3-venv git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libtinfo5 cmake libffi-dev libssl-dev" ;}

echo "[3/4] 构建 APK（首次约需 20-40 分钟，下载 Android SDK/NDK）..."
cd "$WSL_DIR" 2>/dev/null || true
wsl -d Ubuntu-22.04 -- bash -lc "cd $WSL_DIR && python3 -m buildozer -v android debug"

echo "[4/4] 收集产物..."
OUT_DIR="$(pwd)/bin"
mkdir -p "$OUT_DIR"
wsl -d Ubuntu-22.04 -- bash -lc "find $WSL_DIR/bin -name '*.apk' -exec cp {} '$OUT_DIR/' \;"

echo ""
echo "=============================================="
ls -la "$OUT_DIR"/*.apk 2>/dev/null || echo "未找到 APK，请检查上方日志"
echo "构建完成：v${VERSION}"