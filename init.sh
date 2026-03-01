#!/bin/bash

# 财务分析平台 - 初始化脚本

set -e

echo "╔════════════════════════════════════════╗"
echo "║  财务分析平台 初始化                   ║"
echo "╚════════════════════════════════════════╝"

# 检查基本要求
echo ""
echo "检查环境..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请从 https://nodejs.org 安装"
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo "❌ Python 未安装，请从 https://python.org 安装"
    exit 1
fi

echo "✓ Node.js: $(node --version)"
echo "✓ Python: $(python --version)"
echo ""

# 初始化后端
echo "初始化后端..."
cd backend
npm install
cd ..
echo "✓ 后端依赖安装完成"
echo ""

# 初始化前端
echo "初始化前端..."
cd frontend
npm install
cd ..
echo "✓ 前端依赖安装完成"
echo ""

# 初始化Python财务引擎
echo "初始化Python财务引擎..."
cd finance-engine
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "✓ Virtual environment 创建完成"
fi

# 激活虚拟环境（Windows和Unix兼容）
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

pip install -r requirements.txt
cd ..
echo "✓ 财务引擎依赖安装完成"
echo ""

echo "╔════════════════════════════════════════╗"
echo "║  初始化完成！                         ║"
echo "╠════════════════════════════════════════╣"
echo "║  接下来启动服务：                      ║"
echo "║                                        ║"
echo "║  1. 启动Python财务引擎:               ║"
echo "║     cd finance-engine                 ║"
echo "║     python api_server.py              ║"
echo "║                                        ║"
echo "║  2. 启动Express后端 (新终端):         ║"
echo "║     cd backend                        ║"
echo "║     npm run dev                       ║"
echo "║                                        ║"
echo "║  3. 启动React前端 (新终端):           ║"
echo "║     cd frontend                       ║"
echo "║     npm start                         ║"
echo "║                                        ║"
echo "║  或使用Docker Compose:                ║"
echo "║     docker-compose up -d              ║"
echo "╚════════════════════════════════════════╝"
