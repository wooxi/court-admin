#!/bin/bash

# 朝廷政务管理系统备份脚本

set -e

echo "🏛️  朝廷政务管理系统备份中..."

cd /root/court-admin

# 备份目录
BACKUP_DIR="./data/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份 OpenClaw 配置
if [ -f "/root/.openclaw/openclaw.json" ]; then
    echo "📄 备份 OpenClaw 配置..."
    cp /root/.openclaw/openclaw.json "$BACKUP_DIR/openclaw-backup-$TIMESTAMP.json"
fi

# 备份数据库
echo "🗄️  备份数据库..."
docker compose exec -T mysql mysqldump -ucourt_admin -pcourt_admin_2026 court_admin > "$BACKUP_DIR/mysql-backup-$TIMESTAMP.sql" 2>/dev/null || \
docker-compose exec -T mysql mysqldump -ucourt_admin -pcourt_admin_2026 court_admin > "$BACKUP_DIR/mysql-backup-$TIMESTAMP.sql"

# 压缩备份
echo "📦 压缩备份..."
cd $BACKUP_DIR
tar -czf "court-admin-backup-$TIMESTAMP.tar.gz" \
    "openclaw-backup-$TIMESTAMP.json" \
    "mysql-backup-$TIMESTAMP.sql"

# 清理临时文件
rm "openclaw-backup-$TIMESTAMP.json"
rm "mysql-backup-$TIMESTAMP.sql"

echo ""
echo "✅ 备份完成！"
echo "📦 备份文件：$BACKUP_DIR/court-admin-backup-$TIMESTAMP.tar.gz"
echo ""
