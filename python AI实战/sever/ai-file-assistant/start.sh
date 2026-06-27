#!/bin/bash

echo "正在启动AI文件助手..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3。请先安装Python3。"
    exit 1
fi

# 启动Python后端服务器
echo "正在启动后端服务器..."
python3 agent_zp.py --open-browser &

# 等待服务器启动
sleep 2

echo "AI文件助手已启动！"
echo "Web界面将自动在浏览器中打开。"
echo "如果浏览器未自动打开，请访问 http://localhost:8000"