#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Explorer + Ollama AI 功能测试脚本
在阿里云 ECS 服务器上运行：
    python3 test_ollama.py

测试内容：
  1. Ollama 服务是否在线
  2. 模型是否已下载
  3. 本地 Ollama AI 对话（直接调用 Ollama API）
  4. Code Explorer AI 接口（通过 /api/recommend 调用）
  5. AI 健康检查接口
"""

import json
import urllib.request
import urllib.error
import sys

OLLAMA_URL = "http://localhost:11434"
CE_SERVER_URL = "http://localhost:8765"
MODEL = "qwen2.5:1.5b"

def ok(msg): print(f"\033[92m[PASS]\033[0m {msg}")
def fail(msg): print(f"\033[91m[FAIL]\033[0m {msg}")
def info(msg): print(f"\033[96m[INFO]\033[0m {msg}")
def section(msg): print(f"\n\033[95m{'='*50}\n  {msg}\n{'='*50}\033[0m")

section("测试 1: Ollama 服务状态")
try:
    req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read())
        models = data.get("models", [])
        ok(f"Ollama 在线，已安装 {len(models)} 个模型")
        for m in models:
            info(f"  - {m.get('name')} ({m.get('size', 0)//1024**2}MB)")
except urllib.error.URLError as e:
    fail(f"Ollama 不可访问: {e}")
    sys.exit(1)

section("测试 2: Ollama 直接 AI 对话")
test_payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己"}],
    "stream": False,
    "options": {"temperature": 0.7}
}
try:
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(test_payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
        reply = result.get("message", {}).get("content", "")
        ok(f"AI 回复 ({len(reply)} 字): {reply[:100]}...")
except urllib.error.URLError as e:
    fail(f"AI 对话失败: {e}")

section("测试 3: Code Explorer Ollama 状态接口")
try:
    req = urllib.request.Request(f"{CE_SERVER_URL}/api/ollama-status")
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read())
        ok(f"健康检查: {json.dumps(data, ensure_ascii=False, indent=2)}")
except urllib.error.URLError as e:
    fail(f"Code Explorer 不可访问: {e}")

section("测试 4: Code Explorer /api/recommend 接口")
ce_payload = {
    "messages": [{"role": "user", "content": "推荐几个适合初学者的 Python 项目"}],
    "model": "ollama"
}
try:
    req = urllib.request.Request(
        f"{CE_SERVER_URL}/api/recommend",
        data=json.dumps(ce_payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
        if result.get("success"):
            ok(f"AI 回复: {result.get('response', '')[:150]}...")
        else:
            fail(f"AI 错误: {result.get('error', 'unknown')}")
except Exception as e:
    fail(f"请求失败: {e}")

section("测试完成")
info("如果所有 [PASS] 都通过，说明 AI 功能正常！")
