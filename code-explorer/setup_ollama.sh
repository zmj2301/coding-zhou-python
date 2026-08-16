#!/bin/bash
set -e

# ============ 安装 Ollama (if needed) ============
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama already installed"
fi

# ============ Pull model ============
ollama pull qwen2.5:1.5b || true

# ============ Install wrapper ============
cp /root/wrapper.py /usr/local/lib/ollama/llama-server 2>/dev/null || true
chmod +x /usr/local/lib/ollama/llama-server 2>/dev/null || true

# ============ Start ollama service ============
systemctl restart ollama 2>/dev/null || ollama serve &

# ============ Test ============
echo "Testing Ollama..."
sleep 3
curl -s http://localhost:11434/api/tags | python3 -m json.tool || echo "Ollama not responding"

echo "Done!"
