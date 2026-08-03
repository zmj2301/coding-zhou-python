#!/bin/bash
BASE="https://codingzhou.dpdns.org"

echo "=== 用现存 Key 调用 /api/recommend ==="
curl -sk -X POST "$BASE/api/recommend" \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-2ae5b8bfc5b56fdb7905c4bbdbca30b83e379deeadd60acd' \
  -d '{"messages":[{"role":"user","content":"用一句话介绍你自己"}]}' | head -c 600
echo ""
