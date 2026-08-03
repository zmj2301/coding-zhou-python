#!/bin/bash
BASE="https://codingzhou.dpdns.org"
COOKIE="/tmp/wg_cookie.txt"
rm -f "$COOKIE"

echo "=== 1. 登录 ==="
curl -sk -c "$COOKIE" -X POST "$BASE/api/login" -H 'Content-Type: application/json' -d '{"username":"zmj2013","password":"ZHOUmj32842510"}'
echo ""

echo "=== 2. auth-check (带 cookie) ==="
curl -sk -b "$COOKIE" "$BASE/api/auth-check"
echo ""

echo "=== 3. ai-pool (带 cookie) ==="
curl -sk -b "$COOKIE" "$BASE/api/ai-pool?days=7" | python3 -c 'import sys,json; d=json.load(sys.stdin); print("pool:", json.dumps(d.get("pool",{}), ensure_ascii=False)[:200]); print("users:", len(d.get("users",[])))'
echo ""

echo "=== 4. api-keys 列表 (带 cookie) ==="
curl -sk -b "$COOKIE" "$BASE/api/api-keys"
echo ""

echo "=== 5. recommend 通过 API Key 认证测试 ==="
CREATE=$(curl -sk -b "$COOKIE" -X POST "$BASE/api/api-keys" -H 'Content-Type: application/json' -d '{"name":"auth-test"}')
echo "CREATE: $CREATE"
APIKEY=$(echo "$CREATE" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("key",""))')
if [ -n "$APIKEY" ]; then
  curl -sk -X POST "$BASE/api/recommend" -H 'Content-Type: application/json' -H "Authorization: Bearer $APIKEY" -d '{"messages":[{"role":"user","content":"你好"}]}' | python3 -c 'import sys,json; d=json.load(sys.stdin); print("recommend-by-key success:", d.get("success"))'
fi
