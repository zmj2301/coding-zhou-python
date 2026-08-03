#!/bin/bash
echo "=== ai_usage 表 ==="
sqlite3 -header -column /home/code-explorer/data/users.db "SELECT id, user_id, username, date, count, last_active FROM ai_usage;"
echo ""
echo "=== api_keys 表 ==="
sqlite3 -header -column /home/code-explorer/data/users.db "SELECT id, user_id, username, name, key, created_at, last_used_at, is_active FROM api_keys;"
echo ""
echo "=== 服务器日志中最近的 recommend 调用 ==="
journalctl -u code-explorer --no-pager --since "30 min ago" 2>/dev/null | grep -iE "recommend|AI|usage|error" | tail -20
