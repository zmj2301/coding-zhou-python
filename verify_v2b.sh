#!/bin/bash
BASE="https://codingzhou.dpdns.org"
COOKIE="/tmp/wg.txt"

echo "=== 我的 Keys ==="
curl -sk -b "$COOKIE" "$BASE/api/api-keys"
echo ""
echo ""
echo "=== 管理员全部 Keys ==="
curl -sk -b "$COOKIE" "$BASE/api/api-keys?all=1"
echo ""
