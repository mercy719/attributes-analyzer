#!/bin/bash

# 产品属性增强工具 - 新UI版本启动脚本

echo "🚀 启动产品属性增强工具 (新UI版本)"
echo "======================================="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 python -m venv venv"
    exit 1
fi

# 激活虚拟环境
echo "📦 激活虚拟环境..."
source venv/bin/activate

# 检查依赖
echo "🔍 检查Python依赖..."
pip install -r requirements.txt

# 检查API密钥
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠️  警告: 未设置DEEPSEEK_API_KEY环境变量"
    echo "请设置API密钥: export DEEPSEEK_API_KEY='你的密钥'"
fi

# 启动后端API服务
echo "🔧 启动后端API服务..."
echo "API服务将运行在: http://localhost:5001"
python api_app.py &
API_PID=$!

# 等待API服务启动
sleep 3

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    echo "请安装Node.js: https://nodejs.org/"
    echo "或使用Homebrew: brew install node"
    echo ""
    echo "API服务已启动，您可以："
    echo "1. 安装Node.js后手动启动前端"
    echo "2. 直接使用API服务 (http://localhost:5001)"
    echo ""
    echo "按 Ctrl+C 停止API服务"
    wait $API_PID
    exit 1
fi

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装，请重新安装Node.js"
    kill $API_PID
    exit 1
fi

# 进入前端目录
cd frontend

# 检查前端依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动前端开发服务器
echo "🎨 启动前端开发服务器..."
echo "前端界面将运行在: http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

# 等待前端启动
sleep 5

echo ""
echo "🎉 启动成功！"
echo "======================================="
echo "🌐 前端界面: http://localhost:5173"
echo "🔧 API服务:  http://localhost:5001"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $API_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

wait
