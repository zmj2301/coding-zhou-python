Code Explorer - AI Agent Operations Manual

See local file AGENTS.md for full content.

Key operations:
1. Cloudflare Worker deploy: python build.py && npx wrangler deploy
2. KV cache clear: delete all cache: prefixed keys in CODE_EXPLORER_KV namespace
3. ECS restart: ssh root@39.107.96.165 -> pkill -f ecs-server.py -> cd /home/code-explorer -> source ecs-env.sh -> nohup python3 ecs-server.py &
4. ECS health check: curl http://localhost:8765/api/health
5. Cloudflare API Token: set CLOUDFLARE_API_TOKEN env var (account d6b8ca32610afe0fd9407736b9266cb3)
6. Node.js path: C:\Users\Administrator\.trae-cn\binaries\node\versions\24.13.0\node.exe (add to PATH manually)

For full AGENTS.md content, see local workspace file.