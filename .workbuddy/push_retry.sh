#!/bin/bash
# GitHub push 自动重试（网络不稳定，最多 10 次，每 60 秒一次）
cd "E:/coding-zhou/Python"
for i in $(seq 1 10); do
  echo "=== 第 $i 次尝试 $(date +%H:%M:%S) ==="
  if git push origin main 2>&1; then
    echo "PUSH_OK on attempt $i"
    exit 0
  fi
  sleep 60
done
echo "PUSH_FAILED_AFTER_10"
exit 1
