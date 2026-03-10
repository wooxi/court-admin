#!/bin/bash

# 朝廷政务管理系统启动脚本

set -e

echo "🏛️  朝廷政务管理系统启动中..."

# 进入项目目录
cd /root/court-admin

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 检查 MySQL 数据目录
if [ ! -d "./data" ]; then
    echo "📁 创建数据目录..."
    mkdir -p ./data/backups
    mkdir -p ./logs
fi

# 停止旧容器
echo "🛑 停止旧容器..."
docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true

# 启动服务
echo "🚀 启动服务..."
docker compose up -d || docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker compose ps || docker-compose ps

echo ""
echo "✅ 启动完成！"
echo ""
echo "📋 访问地址:"
echo "   前端：http://localhost:9002"
echo "   后端 API: http://localhost:9001"
echo "   后端文档：http://localhost:9001/docs"
echo "   MySQL: localhost:9003"
echo ""
echo "📝 查看日志:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 停止服务:"
echo "   docker-compose down"
echo ""
