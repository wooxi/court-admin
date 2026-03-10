#!/bin/bash

# 朝廷政务管理系统 - 原生停止脚本

set -e

echo "🏛️  朝廷政务管理系统停止中..."

cd /root/court-admin

# 读取 PID
if [ -f "./logs/backend.pid" ]; then
    BACKEND_PID=$(cat ./logs/backend.pid)
    echo "🛑 停止后端服务 (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    rm ./logs/backend.pid
fi

if [ -f "./logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat ./logs/frontend.pid)
    echo "🛑 停止前端服务 (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
    rm ./logs/frontend.pid
fi

# 清理残留进程
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

echo ""
echo "✅ 服务已停止"
echo ""
