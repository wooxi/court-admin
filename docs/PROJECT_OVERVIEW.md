# 🏛️ 朝廷政务管理系统 - 项目说明

## 项目概述

朝廷政务管理系统是一套用于管理 OpenClaw 六部大臣、任务流转、统计报表的 Web 应用系统。

## 核心设计原则

### 1. 任务流转原则 ⭐

```
皇上 → 司礼监 → 六部 → 司礼监 → 皇上
```

- **皇上只对接司礼监**：不直接调度六部
- **司礼监负责任务分析和大臣调度**：根据任务类型分派给合适的大臣
- **六部只接收司礼监的分派**：专注执行
- **所有任务流转记录完整链路**：可追踪、可审计

### 2. 配置管理原则 ⭐

- **先从配置文件获取可用模型列表**：修改大臣模型前，必须读取 openclaw.json
- **字段规范必须符合 OpenClaw 要求**：不确定的字段必须提出，不能臆想猜测
- **修改前必须备份**：自动生成配置文件备份
- **修改后必须热重载**：无需重启 OpenClaw

### 3. 数据库选型 ⭐

- **MySQL 8.0**：皇上指定
- **稳定可靠**：成熟的关系型数据库
- **兼容性好**：广泛的工具和社区支持

### 4. 代码协作规范 ⭐

- 本项目任何改动（代码/文档/配置）都必须完成 `git commit` 并推送到 GitHub 远端分支。
- 禁止仅保留本地改动作为交付结果。
- 未经明确批准，禁止 force push。

## 系统架构

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | Python FastAPI | 轻量高效、异步支持 |
| 前端 | Vue 3 + Element Plus | 朝廷深色主题、组件丰富 |
| 数据库 | MySQL 8.0 | 关系型数据库 |
| 部署 | Docker + Docker Compose | 容器化部署 |

### 端口规划

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 9002 | Vue 3 静态资源 |
| 后端 API | 9001 | FastAPI 服务 |
| MySQL | 9003 | 数据库服务 |
| Nginx | 80/443 | 反向代理（生产） |

## 功能模块

### 1. 大臣配置管理

**功能：**
- 查看六部大臣列表
- 配置每部模型（从配置文件获取可用模型）
- 配置工作区路径
- 启用/禁用大臣

**流程：**
```
用户点击编辑 → 读取 openclaw.json → 解析可用模型 → 显示下拉选择 → 保存 → 备份 → 热重载
```

### 2. 任务管理

**功能：**
- 任务列表（支持筛选、搜索）
- 任务详情查看
- 手动创建任务
- 从 OpenClaw 同步任务

**任务状态：**
- `pending` - 待处理
- `processing` - 进行中
- `completed` - 已完成

### 3. 任务流转追踪 ⭐

**功能：**
- 完整流转链可视化
- 司礼监调度逻辑展示
- 流转图展示

**流转记录：**
- `from_actor` - 发起方
- `to_actor` - 接收方
- `action` - 动作类型
- `remark` - 备注
- `timestamp` - 时间戳

### 4. 统计报表

**功能：**
- Token 用量统计（按大臣/按日）
- 任务数量统计
- 效率分析（平均处理时长）
- 任务执行明细（每次完成任务一条，支持按大臣/时间筛选与分页）

**统计口径：**
- 任务执行明细仅统计功能启用后新产生的完成任务
- 不做历史回填，不追溯旧任务

### 5. OpenClaw 配置管理

**功能：**
- 查看当前配置
- 编辑模型配置
- 配置备份与恢复
- 热重载

**配置字段规范：**

| 配置项 | 字段路径 | 必填 |
|--------|---------|------|
| 模型 ID | `models.providers[].models[].id` | ✅ |
| 大臣模型 | `agents.list[].model.primary` | ✅ |
| 工作区 | `agents.list[].workspace` | ❌ |
| 人设主题 | `agents.list[].identity.theme` | ❌ |

## 数据库设计

### 核心表

1. **ministers** - 大臣配置表
2. **tasks** - 任务表
3. **task_flows** - 任务流转表
4. **task_execution_details** - 任务执行明细表（完成任务的 Token/耗时快照）
5. **token_usage** - Token 用量表
6. **openclaw_config** - 配置表

### 表关系

```
ministers (1) ──< (N) tasks (assignee)
ministers (1) ──< (N) tasks (dispatcher)
tasks (1) ──< (N) task_flows
tasks (1) ──< (0..1) task_execution_details
ministers (1) ──< (N) task_execution_details
ministers (1) ──< (N) token_usage
```

## 部署方式

### Docker Compose（推荐）

```bash
cd /root/court-admin
docker-compose up -d
```

### 服务列表

- `court-admin-mysql` - MySQL 数据库
- `court-admin-backend` - 后端 API 服务
- `court-admin-frontend` - 前端 Web 服务
- `court-admin-nginx` - Nginx 反向代理（生产环境）

## API 设计

### 大臣管理

```
GET    /api/ministers          # 获取大臣列表
POST   /api/ministers          # 创建大臣
PUT    /api/ministers/:id      # 更新大臣
DELETE /api/ministers/:id      # 删除大臣
```

### 模型管理

```
GET    /api/models/available   # 获取可用模型列表
GET    /api/models/schema      # 获取模型配置 Schema
```

### 任务管理

```
GET    /api/tasks              # 获取任务列表
POST   /api/tasks              # 创建任务
PUT    /api/tasks/:id          # 更新任务
```

### 流转追踪

```
GET    /api/flows/task/:id     # 获取任务流转链
POST   /api/flows              # 添加流转记录
```

### 统计报表

```
GET    /api/stats/token             # Token 用量统计
GET    /api/stats/tasks             # 任务统计
GET    /api/stats/efficiency        # 效率统计
GET    /api/stats/task-executions   # 任务执行明细 + 聚合统计（仅启用后新数据）
```

### 配置管理

```
GET    /api/config             # 获取配置
PUT    /api/config/ministers/:id  # 更新大臣配置
POST   /api/config/backup      # 备份配置
POST   /api/config/reload      # 热重载配置
```

## 前端设计

### 配色方案（朝廷深色主题）

- 主色：`#6A9EFF`
- 背景：`#07090F`
- 面板：`#0F1219`
- 文字：`#DDE4F8`
- 边框：`#1C2236`

### 页面布局

- 左侧核心菜单固定为：**总览 / 大臣 / 任务 / 流转 / 定时 / 报表 / 配置**
- 路由与菜单文案必须使用朝廷政务语义，不得替换为电商语义。

```
┌──────────────┬────────────────────────────────┐
│              │                                │
│  左侧菜单    │          顶部栏                │
│              ├────────────────────────────────┤
│  📊 总览     │                                │
│  👥 大臣     │          内容区                │
│  📋 任务     │                                │
│  🔗 流转     │                                │
│  📈 报表     │                                │
│  ⚙️ 配置     │                                │
│              │                                │
└──────────────┴────────────────────────────────┘
```

## 安全考虑

### API Key 管理

- 加密存储（使用 cryptography 库）
- 不在日志中输出
- 前端显示时脱敏

### 配置备份

- 自动备份（修改前）
- 手动备份（用户触发）
- 备份恢复功能

### 权限控制

- TODO: 实现用户认证
- TODO: 实现角色权限
- TODO: 实现 API 限流

## 待实现功能

1. **OpenClaw 热重载集成** - 调用 OpenClaw API 重新加载配置
2. **用户认证系统** - 登录、JWT Token、权限控制
3. **任务自动同步** - 从 OpenClaw 自动同步任务数据
4. **Token 用量深度采集** - 已支持任务完成时落库明细，后续补充对更多上游来源的自动采集
5. **飞书通知集成** - 任务状态变更通知
6. **数据导出** - CSV/Excel 导出
7. **单元测试** - 后端和前端的单元测试

## 项目文件位置

- **项目根目录**: `/root/court-admin`
- **后端代码**: `/root/court-admin/backend/app`
- **前端代码**: `/root/court-admin/frontend/src`
- **Docker 配置**: `/root/court-admin/docker`
- **数据目录**: `/root/court-admin/data`
- **日志目录**: `/root/court-admin/logs`

## 相关文档

- **设计文档**: 飞书云文档 https://www.feishu.cn/docx/ZdaedbeeUon8UJxc7jkckVwmnod
- **API 文档**: http://localhost:9001/docs (启动后访问)
- **README**: `/root/court-admin/README.md`

---

*创建时间：2026-03-10*  
*版本：v2.0.0*
