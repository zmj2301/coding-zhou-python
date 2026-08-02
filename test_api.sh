#!/bin/bash
LOGIN=$(curl -s -X POST http://localhost/api/login -H 'Content-Type: application/json' -d '{"username":"zmj2013","password":"zmj2013"}')
echo "LOGIN: $LOGIN"
TOKEN=$(echo "$LOGIN" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("token",""))')
echo "TOKEN: $TOKEN"

CREATE=$(curl -s -X POST http://localhost/api/api-keys -H 'Content-Type: application/json' -b "wg_token=$TOKEN" -d '{"name":"Test Key 123"}')
echo "CREATE: $CREATE"

LIST=$(curl -s http://localhost/api/api-keys -b "wg_token=$TOKEN")
echo "LIST: $LIST"
