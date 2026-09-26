#!/bin/bash
cd /tmp
rm -f ollama.tgz

echo "=== Downloading Ollama tarball from ollama.com (10 min timeout) ==="
curl -L --connect-timeout 30 --max-time 600 -o ollama.tgz 'https://ollama.com/download/ollama-linux-amd64.tgz' 2>&1 | tail -3

if [ -f ollama.tgz ]; then
  SIZE=$(stat -c%s ollama.tgz 2>/dev/null || echo 0)
  echo "Downloaded size: $SIZE bytes"
  if [ "$SIZE" -gt 1000000 ]; then
    echo "=== Extracting llama-server ==="
    mkdir -p /tmp/ollama-extract
    tar xzf ollama.tgz -C /tmp/ollama-extract 2>&1 | tail -3
    echo "Extracted files:"
    find /tmp/ollama-extract -name 'llama-server' -type f 2>/dev/null
    
    LLAMA_SERVER=$(find /tmp/ollama-extract -name 'llama-server' -type f | head -1)
    if [ -n "$LLAMA_SERVER" ]; then
      echo "Found llama-server: $LLAMA_SERVER"
      echo "ldd check:"
      ldd "$LLAMA_SERVER" 2>&1 | grep -E "not found" || echo "  OK: no missing libraries"
      
      echo ""
      echo "=== Installing llama-server ==="
      systemctl stop ollama 2>/dev/null || true
      cp "$LLAMA_SERVER" /usr/local/lib/ollama/llama-server
      chmod +x /usr/local/lib/ollama/llama-server
      echo "Installed to /usr/local/lib/ollama/llama-server"
      
      echo ""
      echo "=== Starting Ollama ==="
      systemctl start ollama
      sleep 5
      systemctl status ollama --no-pager -n 3 2>&1 | head -6
      
      echo ""
      echo "=== Testing Ollama ==="
      curl -s http://127.0.0.1:11434/api/tags | head -c 300
      echo ""
    else
      echo "ERROR: llama-server not found in tarball"
      echo "Tarball contents:"
      tar tzf ollama.tgz | head -20
    fi
  else
    echo "ERROR: Downloaded file too small ($SIZE bytes)"
  fi
else
  echo "ERROR: Download failed"
fi

echo ""
echo "=== Cleanup ==="
rm -rf /tmp/ollama-extract ollama.tgz
