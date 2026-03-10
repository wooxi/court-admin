#!/bin/bash

# 朝廷政务管理系统停止脚本

set -e

echo "🏛️  朝廷政务管理系统停止中..."

cd /root/court-admin

# 停止服务
docker compose down || docker-compose down

echo ""
echo "✅ 服务已停止"
echo ""
echo "📝 如需删除数据卷（谨慎操作）:"
echo "   docker compose down -v"
echo ""
