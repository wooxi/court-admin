#!/bin/bash

# 朝廷政务管理系统 - 原生重启脚本

set -e

echo "🏛️  朝廷政务管理系统重启中..."

# 停止服务
/root/court-admin/scripts/stop-native.sh

# 等待
sleep 2

# 启动服务
/root/court-admin/scripts/start-native.sh
