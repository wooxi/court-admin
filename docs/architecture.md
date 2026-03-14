# 架构总览（OpenClaw 管理中枢）

## 1. 这套系统是什么

court-admin 不是单页面，而是 OpenClaw 朝廷体系的管理中枢：

- **控制面**：统一查看/管理大臣（agents）与模型（models）配置。
- **执行面**：承接司礼监分派后的任务记录、状态推进、流转链路。
- **统计面**：沉淀 TOKEN 与耗时，形成统一报表口径。

> 目标：让“分派机制”可追踪、“执行质量”可量化、“配置变更”可审计。

---

## 2. 四层架构

## 2.1 调度层（司礼监）

职责：
1. 领旨
2. 任务拆解
3. 分派六部
4. 追踪与验收
5. 回奏

关键机制：
- 子会话分派：`sessions_spawn(...)`
- 强制分派守卫：`dispatch_guard.dispatch_with_guard(...)`

## 2.2 执行层（六部）

- 兵部：软件工程
- 户部：财务/数据
- 礼部：内容/品牌
- 工部：运维部署
- 吏部：项目管理
- 刑部：法务合规

六部只接收司礼监分派，不直接承接皇上指令。

## 2.3 政务系统（任务/流转/统计）

核心表：
- `tasks`：任务主表
- `task_flows`：任务流转日志
- `task_execution_details`：完成任务的 TOKEN/耗时快照

## 2.4 配置中心（agents 与模型）

- 读取/同步 OpenClaw 配置。
- 统一管理大臣启停、模型主配、工作区路径。
- 支持配置热更新（由 OpenClaw 侧配合）。

---

## 3. 分派机制（标准链路）

标准流程：

```text
领旨 → 拆解 → 分派 → 追踪 → 验收 → 回奏
```

工程任务默认必须分派：
- 入口：`dispatch_with_guard(...)`
- 守卫校验 5 项必填：任务拆解、承办部门、分派声明、ETA、汇报证据
- 校验通过后才允许 `sessions_spawn`

### 3.1 sessions_spawn 子会话机制

典型参数：

```python
sessions_spawn(
    agentId="gongbu",
    task="[任务ID: TASK-...] ...",
    mode="run",
    streamTo="parent",
    timeoutSeconds=1800,
)
```

### 3.2 强制分派规则与例外

默认规则：
- 开发/重构/修复/部署/联调/验收类任务：**必须分派**。

允许不分派的例外：
1. 皇上明确要求“司礼监自行执行”。
2. 纯信息查询或极简一次性操作。

若不分派，必须在汇报中明确声明“本次未分派，司礼监自行执行”。

---

## 4. 任务记录机制

## 4.1 create_task / update_task_status / task_flow

司礼监脚本（位于 `/root/clawd/silijian`）与本系统 API 对接：

- `create_task(...)` → `POST /api/tasks`
- `update_task_status(...)` → `PUT /api/tasks/{id}`
- `record_task_flow(...)` → `POST /api/tasks/{id}/flows`

流转字段采用：
- `from_actor`
- `to_actor`
- `action`
- `remark`
- `metadata`

## 4.2 task_tracker 自动追踪与完成回写

追踪逻辑：
1. 分派成功后 `track_task(session_key, task_id)` 建立映射。
2. 子会话 completion event 触发 `complete_task(...)`。
3. 自动回写任务状态为 `completed`，并带上 token/耗时。

## 4.3 TOKEN 与耗时入报表

当任务状态更新为 `completed` 且包含统计字段时，后端会把以下数据幂等写入 `task_execution_details`：

- `input_tokens`
- `output_tokens`
- `total_tokens`
- `duration_seconds`
- `session_key`
- `completed_at`

这张表是报表主数据源。

---

## 5. 统计口径（统一版）

- 任务状态类统计：来自 `tasks`
- TOKEN/耗时统计：来自 `task_execution_details`
- **启用前历史不回填**：只统计启用后新产生且成功写入明细表的数据

该口径在 README、部署、运维、FAQ 文档中保持一致。
