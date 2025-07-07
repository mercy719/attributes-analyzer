#!/bin/bash

# 产品属性增强工具部署脚本
# 使用方法: ./deploy.sh [local|docker|build]

set -e

echo "🚀 产品属性增强工具部署脚本"
echo "=================================="

# 获取部署类型
DEPLOY_TYPE=${1:-local}

case $DEPLOY_TYPE in
    "local")
        echo "📦 本地部署模式"
        echo "正在检查Python环境..."
        
        # 检查Python版本
        python3 --version
        
        # 创建虚拟环境（如果不存在）
        if [ ! -d "venv" ]; then
            echo "创建虚拟环境..."
            python3 -m venv venv
        fi
        
        # 激活虚拟环境
        source venv/bin/activate
        
        # 安装依赖
        echo "安装依赖..."
        pip install -r requirements.txt
        
        # 创建必要目录
        mkdir -p uploads results
        
        # 启动应用
        echo "启动应用..."
        echo "应用将在 http://localhost:5001 运行"
        python app.py
        ;;
        
    "docker")
        echo "🐳 Docker部署模式"
        
        # 构建Docker镜像
        echo "构建Docker镜像..."
        docker build -t air-styler-app .
        
        # 运行Docker容器
        echo "启动Docker容器..."
        docker run -d \
            --name air-styler-app \
            -p 5001:5001 \
            -v $(pwd)/uploads:/app/uploads \
            -v $(pwd)/results:/app/results \
            -v $(pwd)/tasks.json:/app/tasks.json \
            air-styler-app
        
        echo "应用已启动在 http://localhost:5001"
        echo "使用 'docker logs air-styler-app' 查看日志"
        echo "使用 'docker stop air-styler-app' 停止应用"
        ;;
        
    "build")
        echo "🔨 仅构建Docker镜像"
        docker build -t air-styler-app .
        echo "镜像构建完成: air-styler-app"
        ;;
        
    *)
        echo "❌ 无效的部署类型: $DEPLOY_TYPE"
        echo "使用方法: ./deploy.sh [local|docker|build]"
        echo "  local  - 本地Python环境部署"
        echo "  docker - Docker容器部署"
        echo "  build  - 仅构建Docker镜像"
        exit 1
        ;;
esac

echo "✅ 部署完成!" 