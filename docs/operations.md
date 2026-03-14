# 运维手册（启动、重启、日志、备份、回滚）

## 1. 服务启停

### 1.1 Docker 模式

```bash
cd /root/court-admin
docker compose up -d
docker compose ps
```

停止：

```bash
cd /root/court-admin
docker compose down
```

重启（全量）：

```bash
cd /root/court-admin
docker compose restart
```

单服务重启：

```bash
cd /root/court-admin
docker compose restart backend
docker compose restart frontend
docker compose restart mysql
```

### 1.2 OpenClaw 网关

```bash
openclaw gateway status
openclaw gateway restart
```

---

## 2. 日志查看

### 2.1 Docker 日志

```bash
cd /root/court-admin
docker compose logs -f --tail=200 backend
docker compose logs -f --tail=200 frontend
docker compose logs -f --tail=200 mysql
```

### 2.2 本地目录日志

```bash
cd /root/court-admin
ls -lah logs
```

---

## 3. 备份策略

## 3.1 数据库备份（每日）

```bash
cd /root/court-admin
set -a; source .env; set +a
mkdir -p data/backups

docker compose exec -T mysql \
  mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" \
  --single-transaction --default-character-set=utf8mb4 \
  court_admin > "data/backups/court_admin-$(date +%Y%m%d-%H%M%S).sql"
```

## 3.2 OpenClaw 配置备份

```bash
mkdir -p /root/court-admin/data/backups
cp ~/.openclaw/openclaw.json \
  "/root/court-admin/data/backups/openclaw-$(date +%Y%m%d-%H%M%S).json"
```

---

## 4. 回滚流程

## 4.1 数据库回滚

```bash
cd /root/court-admin
set -a; source .env; set +a

# 示例：回滚到某次备份
BACKUP_FILE=data/backups/court_admin-YYYYMMDD-HHMMSS.sql

docker compose exec -T mysql \
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" court_admin < "$BACKUP_FILE"
```

## 4.2 OpenClaw 配置回滚

```bash
cp /root/court-admin/data/backups/openclaw-YYYYMMDD-HHMMSS.json ~/.openclaw/openclaw.json
openclaw gateway restart
```

---

## 5. 健康检查与关键 API 简测

## 5.1 健康检查

```bash
curl -fsS http://127.0.0.1:9001/health
curl -fsS http://127.0.0.1:9001/api/ministers | head -c 200 && echo
```

## 5.2 任务主链路冒烟

```bash
# 1) 创建任务
TASK_CODE="TASK-SMOKE-$(date +%s)"
TASK_PAYLOAD=$(cat <<JSON
{
  "task_id": "${TASK_CODE}",
  "title": "smoke test",
  "description": "ops smoke",
  "assignee_id": 2,
  "dispatcher_id": 1,
  "status": "pending",
  "priority": "medium"
}
JSON
)

TASK_CREATE=$(curl -fsS -X POST http://127.0.0.1:9001/api/tasks \
  -H 'Content-Type: application/json' \
  -d "$TASK_PAYLOAD")

echo "$TASK_CREATE"
TASK_PK=$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["id"])' <<< "$TASK_CREATE")

# 2) 查任务
curl -fsS "http://127.0.0.1:9001/api/tasks/by-code/${TASK_CODE}"

# 3) 更新状态（含 token/耗时，触发执行明细写入）
curl -fsS -X PUT "http://127.0.0.1:9001/api/tasks/${TASK_PK}" \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "completed",
    "input_tokens": 10,
    "output_tokens": 15,
    "total_tokens": 25,
    "duration_seconds": 8,
    "source": "ops_smoke"
  }'
```

---

## 6. 报表口径提醒（避免误判）

- `task_execution_details` 只记录启用后新完成任务。
- 旧任务不会自动补历史 TOKEN/耗时。
- 如果报表初期数据少，这是设计口径，不是故障。
