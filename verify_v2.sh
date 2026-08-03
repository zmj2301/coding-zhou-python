#!/bin/bash
BASE="https://codingzhou.dpdns.org"
COOKIE="/tmp/wg.txt"
rm -f "$COOKIE"

echo "=== 1. 登录 ==="
curl -sk -c "$COOKIE" -X POST "$BASE/api/login" -H 'Content-Type: application/json' -d '{"username":"zmj2013","password":"ZHOUmj32842510"}' -o /dev/null
echo "login done"

echo "=== 2. 创建带完整字段的 Key ==="
curl -sk -b "$COOKIE" -X POST "$BASE/api/api-keys" -H 'Content-Type: application/json' -d '{"name":"测试-爬虫","desc":"抓取数据用","daily_limit":50,"expires_at":'$(($(date +%s)+604800))'}' | python3 -m json.tool 2>/dev/null || echo "(raw output above)"

echo "=== 3. 列出我的 Keys（应含新字段）==="
curl -sk -b "$COOKIE" "$BASE/api/api-keys" | python3 -c '
import sys,json
d=json.load(sys.stdin)
for k in d["keys"]:
    print(f"id={k[\"id\"]} name={k[\"name\"]} desc={k.get(\"desc\")} limit={k.get(\"daily_limit\")} expires={k.get(\"expires_at\")} active={k[\"is_active\"]}")
'

echo "=== 4. 管理员查看全部 ==="
curl -sk -b "$COOKIE" "$BASE/api/api-keys?all=1" | python3 -c '
import sys,json
d=json.load(sys.stdin)
print(f"总key数: {len(d[\"keys\"])}")
for k in d["keys"]:
    print(f"  {k[\"username\"]}: {k[\"name\"]} active={k[\"is_active\"]}")
'

echo "=== 5. 测试 toggle（禁用第1个key再启用）==="
ID=$(curl -sk -b "$COOKIE" "$BASE/api/api-keys" | python3 -c 'import sys,json; print(json.load(sys.stdin)["keys"][0]["id"])')
echo "目标 key id: $ID"
curl -sk -b "$COOKIE" "$BASE/api/api-keys/toggle?id=$ID"
echo ""
curl -sk -b "$COOKIE" "$BASE/api/api-keys/toggle?id=$ID"
echo ""

echo "=== 6. 删除测试key ==="
NEWID=$(curl -sk -b "$COOKIE" "$BASE/api/api-keys" | python3 -c 'import sys,json; print(json.load(sys.stdin)["keys"][0]["id"])')
echo "删除 id: $NEWID"
curl -sk -b "$COOKIE" "$BASE/api/api-keys/delete?id=$NEWID"
echo ""
