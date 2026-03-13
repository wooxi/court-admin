# 🏛️ 朝廷政务管理系统

> AI 朝廷架构 · 司礼监统领六部 · 政务处理自动化

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/wooxi/court-admin)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📋 项目简介

朝廷政务管理系统是一个基于 AI Agent 的任务调度与政务处理系统，采用传统朝廷架构设计，实现任务的自动化分派、执行、追踪和归档。

**核心理念：**
- 🏛️ **朝廷架构** — 司礼监统领六部，层级清晰
- 🤖 **AI Agent** — 六部尚书均为 AI Agent，7×24 小时工作
- 📊 **政务系统** — 完整的任务管理、流转追踪、统计报表
- 🔔 **实时通知** — 飞书集成，任务状态实时推送

---

## 🏛️ 朝廷架构

### 权力结构

```
                    ┌─────────────┐
                    │   皇  帝    │
                    │  (用户)     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   司礼监    │
                    │ (大内总管)  │
                    │  任务调度   │
                    └──────┬──────┘
                           │ 分派任务
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │  兵 部  │      │  户 部  │      │  礼 部  │
    │ ⚔️软件工程│      │ 💰财务预算│      │ 🎨品牌营销│
    └─────────┘      └─────────┘      └─────────┘
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │  工 部  │      │  吏 部  │      │  刑 部  │
    │ 🔧运维部署│      │ 📋项目管理│      │ ⚖️法务合规│
    └─────────┘      └─────────┘      └─────────┘
```

### 六部职责

| 部门 | 封号 | Emoji | 职责 | 模型 |
|------|------|-------|------|------|
| **司礼监** | 大内总管 | 🏛️ | 调度六部、日常对话、任务分派 | qwen3.5-plus |
| **兵部** | 镇国大将军 | ⚔️ | 软件工程、系统架构、代码审查 | qwen3-coder-plus |
| **户部** | 镇国财神 | 💰 | 财务预算、成本管控、电商运营 | qwen3.5-plus |
| **礼部** | 文华殿大学士 | 🎨 | 品牌营销、社交媒体、内容创作 | kimi-k2.5 |
| **工部** | 将作监大匠 | 🔧 | DevOps、服务器运维、CI/CD | qwen3-coder-next |
| **吏部** | 文渊阁大学士 | 📋 | 项目管理、创业孵化、团队协调 | qwen3.5-plus |
| **刑部** | 大理寺卿 | ⚖️ | 法务合规、知识产权、合同审查 | qwen3-max |

---

## 🔧 技术架构

### 系统组成

```
court-admin/
├── backend/              # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── models/      # 数据模型
│   │   └── main.py      # 入口文件
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # 前端服务 (Vue 3)
│   ├── src/
│   │   ├── views/      # 页面组件
│   │   ├── components/ # 通用组件
│   │   └── api/        # API 调用
│   ├── package.json
│   └── Dockerfile
├── docker/             # Docker 配置
│   ├── mysql-init.sql  # 数据库初始化
│   └── nginx.conf      # Nginx 配置
├── data/               # 数据目录
├── logs/               # 日志目录
└── docker-compose.yml  # Docker Compose 配置
```

### 技术栈

**后端：**
- FastAPI + SQLAlchemy + MySQL
- 任务调度 + 流转追踪
- RESTful API

**前端：**
- Vue 3 + Element Plus
- 实时数据刷新
- 流转时间线展示

**AI Agent：**
- OpenClaw 框架
- 多 Agent 协作
- 任务自动追踪

---

## 📋 核心功能

### 1. 大臣配置管理
- ✅ 七部大臣配置
- ✅ 模型动态切换
- ✅ 工作区隔离
- ✅ 实时刷新配置

### 2. 任务管理
- ✅ 任务创建/分派/执行/完成
- ✅ 任务状态自动追踪
- ✅ 政务系统任务 ID
- ✅ 角标实时显示待办

### 3. 任务流转追踪 ⭐
- ✅ 完整流转链可视化
- ✅ 司礼监调度逻辑展示
- ✅ 执行日志记录
- ✅ 时间线展示

### 4. 统计报表
- ✅ Token 用量统计
- ✅ 任务数量统计
- ✅ 效率分析
- ✅ 飞书多维表格集成

### 5. 定时任务
- ✅ 服务健康检查（每 5 分钟）
- ✅ 服务自动重启
- ✅ 飞书通知推送
- ✅ 心跳机制保底

### 6. OpenClaw 集成
- ✅ 大臣配置同步
- ✅ 任务自动记录
- ✅ completion event 追踪
- ✅ 会话状态管理

---

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose
- MySQL 8.0+
- Node.js 18+
- Python 3.12+

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/wooxi/court-admin.git
cd court-admin

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 配置数据库、飞书等

# 3. 启动服务
docker-compose up -d

# 4. 访问服务
# 前端：http://localhost:9002
# 后端 API: http://localhost:9001
# API 文档：http://localhost:9001/docs
```

### 配置 OpenClaw

```bash
# 安装 OpenClaw
npm install -g openclaw

# 配置大臣
openclaw agents add silijian --workspace /root/clawd/silijian
openclaw agents add bingbu --workspace /root/clawd/bingbu
# ... 配置其他大臣

# 启动网关
openclaw gateway start
```

---

## 📖 使用指南

### 任务分派流程

1. **皇上旨意** → 司礼监接收
2. **创建任务** → 调用 `task_recorder.create_task()`
3. **分派六部** → 调用 `sessions_spawn()`
4. **开始追踪** → 调用 `task_tracker.track_task()`
5. **自动完成** → completion event 触发状态更新
6. **回奏皇上** → 汇报完成情况

### API 示例

```bash
# 创建任务
curl -X POST http://localhost:9001/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK-20260313-001",
    "title": "修复 API 错误",
    "description": "检查后端服务",
    "assignee_id": 5,
    "dispatcher_id": 1,
    "status": "pending",
    "priority": "high"
  }'

# 获取流转历史
curl http://localhost:9001/api/tasks/1/flows

# 更新任务状态
curl -X PUT http://localhost:9001/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

---

## 📊 数据库设计

### 核心表

**tasks（任务表）**
```sql
- id: 主键
- task_id: 任务 ID（唯一）
- title: 任务标题
- description: 任务描述
- assignee_id: 承办大臣 ID
- dispatcher_id: 调度大臣 ID
- status: 状态（pending/processing/completed）
- priority: 优先级
- agent_session_key: OpenClaw 会话 key
- created_at: 创建时间
- completed_at: 完成时间
```

**task_flows（流转表）**
```sql
- id: 主键
- task_id: 任务 ID
- from_actor: 发起方
- to_actor: 接收方
- action: 动作类型
- remark: 备注
- meta_data: 扩展元数据（JSON）
- created_at: 记录时间
```

**ministers（大臣表）**
```sql
- id: 主键
- name: 大臣名称
- department: 部门
- model_id: 模型 ID
- workspace: 工作区路径
- enabled: 是否启用
```

---

## 🔔 通知机制

### 飞书集成

**通知场景：**
- ✅ 任务分派通知
- ✅ 任务完成通知
- ✅ 服务异常告警
- ✅ 定时任务报告

**配置方式：**
```bash
# .env 配置
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
FEISHU_CHAT_ID=oc_xxxxxxxxxxxxx
```

---

## 📝 开发计划

- [x] 后端框架搭建
- [x] 数据库模型设计
- [x] API 路由实现
- [x] 前端框架搭建
- [x] 大臣管理页面
- [x] 任务管理页面
- [x] 流转追踪页面
- [x] 任务自动记录机制
- [x] completion event 追踪
- [x] 心跳检查机制
- [x] 飞书通知集成
- [ ] 单元测试
- [ ] 性能优化
- [ ] 移动端适配

---

## 📞 联系方式

- **GitHub:** https://github.com/wooxi/court-admin
- **作者:** 王重洋
- **版本:** v2.0.0

---

## 📄 许可证

MIT License

---

*创建时间：2026-03-10*  
*最后更新：2026-03-13*
