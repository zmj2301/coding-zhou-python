#!/bin/bash
# 重启服务
systemctl restart code-explorer
sleep 3
systemctl status code-explorer --no-pager | head -8
echo ""
echo "=== api_keys 表结构 ==="
sqlite3 /home/code-explorer/data/users.db "PRAGMA table_info(api_keys);"
