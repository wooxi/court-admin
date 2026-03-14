# FAQ 与排障（12 条）

## 1) 前端页面空白 / 接口 404

**现象**：前端能打开，但数据全空。

**排查**：
```bash
curl -i http://127.0.0.1:9001/health
curl -i http://127.0.0.1:9001/api/ministers
```

**处理**：
- 后端没起：`docker compose restart backend`
- 前端代理错：检查 `frontend/vite.config.js` 与 Nginx `/api` 代理目标。

---

## 2) `/api/config/*` 返回 401

**原因**：配置了 `CONFIG_ADMIN_TOKEN`，但请求头未带 `X-Admin-Token`。

**处理**：
- 前端设置 token；
- 或在运维脚本中补请求头。

---

## 3) 报表里 TOKEN/耗时一直是 0

**原因**：任务完成时未提交 `input_tokens/output_tokens/total_tokens/duration_seconds`。

**处理**：
- 确认司礼监调用 `update_task_status(...)` 时带上述字段。
- 检查 `task_execution_details` 是否有新记录。

---

## 4) 为什么旧任务没有进入报表？

**这是设计口径**：`task_execution_details` 只统计启用后新完成任务，不回填历史。

---

## 5) `task_flows` 写入失败（字段不存在）

**原因**：数据库结构与当前代码不一致（例如仍是 `actor/details` 旧结构）。

**处理**：
```bash
cd /root/court-admin
set -a; source .env; set +a
for f in backend/sql/*.sql; do
  docker compose exec -T mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" court_admin < "$f"
done
```

---

## 6) OpenClaw 配置读取失败

**排查**：
```bash
echo "$OPENCLAW_CONFIG_PATH"
python3 -m json.tool "$OPENCLAW_CONFIG_PATH" >/dev/null
```

**处理**：
- 路径写错：改 `.env` 的 `OPENCLAW_CONFIG_PATH`
- JSON 非法：修复后 `openclaw gateway restart`

---

## 7) Feishu 消息不进来

**排查顺序**：
1. `openclaw gateway status`
2. 飞书应用回调 / webhook 是否有效
3. 频道配置是否加载到 `openclaw.json`

**处理**：
```bash
openclaw gateway restart
```

---

## 8) CORS 报错（浏览器拦截）

**处理**：检查 `.env` 的 `CORS_ORIGINS`，确保包含当前前端访问地址。

示例：
```dotenv
CORS_ORIGINS=http://localhost:9002,http://127.0.0.1:9002
```

---

## 9) `docker compose up` 后 backend 不断重启

**常见原因**：数据库连不上。

**排查**：
```bash
docker compose logs --tail=200 backend
docker compose logs --tail=200 mysql
```

**处理**：
- 校验 `.env` 中数据库账号密码与 `DATABASE_URL`
- 确认 MySQL 已 ready 后再启动 backend

---

## 10) 任务创建成功但状态不自动完成

**原因**：`task_tracker` 没收到子会话 completion event，或 session_key 未正确追踪。

**处理**：
- 检查 `track_task(session_key, task_id)` 是否执行
- 必要时手动调用 `update_task_status(..., status="completed")`

---

## 11) 数据库中文乱码

**处理**：
- 连接串加 `?charset=utf8mb4`
- MySQL 库表字符集设为 `utf8mb4`
- 重新应用初始化 SQL

---

## 12) 想回滚到昨天版本

**推荐顺序**：
1. 先回滚数据库备份
2. 再回滚 OpenClaw 配置
3. 最后回滚代码并重启服务

参考命令见 [`docs/operations.md`](operations.md) 的“回滚流程”。
