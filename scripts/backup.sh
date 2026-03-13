#!/bin/bash

# 朝廷政务管理系统备份脚本
set -e

echo "🏛️  朝廷政务管理系统备份中..."
cd /root/court-admin

# 载入环境变量
if [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs)
fi

BACKUP_DIR="${BACKUP_DIR:-./data/backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_DIR"

MYSQL_USER="${MYSQL_USER:-court_admin}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}"
MYSQL_DATABASE="${MYSQL_DATABASE:-court_admin}"

if [ -f "/root/.openclaw/openclaw.json" ]; then
  echo "📄 备份 OpenClaw 配置..."
  cp /root/.openclaw/openclaw.json "$BACKUP_DIR/openclaw-backup-$TIMESTAMP.json"
fi

echo "🗄️  备份数据库..."
if [ -z "$MYSQL_PASSWORD" ]; then
  echo "❌ MYSQL_PASSWORD 未配置，无法备份数据库"
  exit 1
fi

if docker compose ps mysql >/dev/null 2>&1; then
  docker compose exec -T mysql mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" > "$BACKUP_DIR/mysql-backup-$TIMESTAMP.sql"
else
  echo "❌ mysql 容器未运行，请先启动 docker compose"
  exit 1
fi

echo "📦 压缩备份..."
cd "$BACKUP_DIR"
tar -czf "court-admin-backup-$TIMESTAMP.tar.gz" \
  "openclaw-backup-$TIMESTAMP.json" \
  "mysql-backup-$TIMESTAMP.sql"

rm -f "openclaw-backup-$TIMESTAMP.json" "mysql-backup-$TIMESTAMP.sql"

echo "✅ 备份完成：$BACKUP_DIR/court-admin-backup-$TIMESTAMP.tar.gz"
