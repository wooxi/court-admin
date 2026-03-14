# court-admin

OpenClaw 朝廷体系的**管理中枢**（不是单页面 Demo）。

它负责把“司礼监调度 + 六部执行 + 政务台账 + 配置中心”落到可运维的系统里：
- 司礼监分派后的任务，在这里留痕、流转、统计。
- 六部模型与工作区配置，在这里统一管理。
- TOKEN 与耗时数据，在这里入库形成报表口径。

---

## 1. 系统定位

court-admin = OpenClaw 管理后端 + 可视化前端 + MySQL 数据层。

核心目标：
1. 让分派机制可审计（谁派给谁、何时完成、证据链）。
2. 让任务执行可量化（完成率、TOKEN、耗时趋势）。
3. 让配置变更可控（agents / models 有统一入口）。

---

## 2. 核心模块

- **调度层（司礼监）**：领旨→拆解→分派→追踪→验收→回奏。
- **执行层（六部）**：兵/户/礼/工/吏/刑，按职责承接子会话。
- **政务系统**：`tasks`、`task_flows`、`task_execution_details`。
- **配置中心**：OpenClaw agents 与 models 管理、同步、校验。

详细架构：见 [`docs/architecture.md`](docs/architecture.md)

---

## 3. 文档导航

- 架构与机制：[`docs/architecture.md`](docs/architecture.md)
- 从零部署：[`docs/deployment.md`](docs/deployment.md)
- 运维手册：[`docs/operations.md`](docs/operations.md)
- 常见问题：[`docs/faq.md`](docs/faq.md)

---

## 4. 快速启动（Docker）

```bash
cd /root/court-admin
docker compose up -d --build
docker compose ps
```

默认端口：
- 前端：`http://localhost:9002`
- 后端 API：`http://localhost:9001`
- Swagger：`http://localhost:9001/docs`
- MySQL：`localhost:9003`

---

## 5. 本地开发（前后端分离）

### 5.1 后端

```bash
cd /root/court-admin/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp -n ../.env.example ../.env
uvicorn app.main:app --host 0.0.0.0 --port 9001 --reload
```

### 5.2 前端

```bash
cd /root/court-admin/frontend
npm install
npm run dev -- --host 0.0.0.0 --port 9002
```

---

## 6. 统计口径（强约束）

- `tasks`：任务状态统计（总数、完成率、按状态分布）
- `task_execution_details`：TOKEN 与耗时明细（报表主来源）
- **不回填历史**：仅统计“该功能启用后”新增完成任务

该口径在架构/部署/运维/FAQ 文档中保持一致。

---

## 7. API 概览

- `GET /health`
- `GET /api/tasks` / `POST /api/tasks` / `PUT /api/tasks/{id}`
- `POST /api/tasks/{id}/flows` / `GET /api/tasks/{id}/flows`
- `GET /api/stats/tasks`
- `GET /api/stats/task-executions`
- `GET /api/stats/task-executions/trend`
- `GET /api/ministers/*`
- `GET|PUT /api/config/*`

---

## 8. Git 约束

- 所有改动必须 commit 并 push 到远端。
- 禁止未经批准的 `force push`。
