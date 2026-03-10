# 🏛️ 朝廷政务管理系统

> 管理 OpenClaw 六部大臣、任务流转、统计报表的 Web 系统

## 📋 项目结构

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
├── docker-compose.yml  # Docker Compose 配置
└── README.md
```

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 进入项目目录
cd /root/court-admin

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 访问服务
# 前端：http://localhost:9002
# 后端 API: http://localhost:9001
# MySQL: localhost:9003
```

### 方式二：本地开发

#### 后端

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 9001
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📊 端口规划

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 9002 | Vue 3 静态资源 |
| 后端 API | 9001 | FastAPI 服务 |
| MySQL | 9003 | 数据库服务 |
| Nginx | 80/443 | 反向代理（生产） |

## 🎯 核心功能

### 1. 大臣配置管理
- 查看六部大臣列表
- 配置每部模型（从 OpenClaw 配置文件获取可用模型）
- 配置工作区路径
- 启用/禁用大臣

### 2. 任务管理
- 任务列表（支持筛选、搜索）
- 任务详情查看
- 手动创建任务
- 从 OpenClaw 同步任务

### 3. 任务流转追踪 ⭐
- 完整流转链可视化
- 司礼监调度逻辑展示
- 流转图展示

### 4. 统计报表
- Token 用量统计
- 任务数量统计
- 效率分析

### 5. OpenClaw 配置管理
- 查看当前配置
- 编辑模型配置（先获取可用列表）
- 配置备份与恢复
- 热重载（待实现）

## ⚙️ 配置说明

### 环境变量

后端服务支持以下环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | mysql+pymysql://... | 数据库连接 URL |
| `OPENCLAW_CONFIG_PATH` | /root/.openclaw/openclaw.json | OpenClaw 配置文件路径 |
| `BACKUP_DIR` | /app/data/backups | 配置备份目录 |

### OpenClaw 配置集成

系统会读取 `/root/.openclaw/openclaw.json` 配置文件：

- **可用模型列表**: `models.providers[].models[]`
- **大臣配置**: `agents.list[]`
- **大臣模型**: `agents.list[].model.primary`

⚠️ **重要原则：**
- 修改配置前必须先备份
- 不确定的字段必须提出，不能臆想猜测
- 修改后需要调用热重载 API

## 📝 API 文档

启动后端后访问：http://localhost:9001/docs

### 主要 API

| 模块 | 路径 | 方法 | 说明 |
|------|------|------|------|
| 大臣管理 | /api/ministers | GET/POST/PUT/DELETE | 大臣 CRUD |
| 模型列表 | /api/models/available | GET | 获取可用模型 |
| 任务管理 | /api/tasks | GET/POST/PUT/DELETE | 任务 CRUD |
| 流转追踪 | /api/flows/task/{id} | GET | 获取流转链 |
| 统计报表 | /api/stats/token | GET | Token 统计 |
| 配置管理 | /api/config | GET/PUT | 配置管理 |

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI
- **ORM**: SQLAlchemy
- **数据库**: MySQL 8.0
- **验证**: Pydantic

### 前端
- **框架**: Vue 3
- **UI 库**: Element Plus
- **路由**: Vue Router
- **状态管理**: Pinia
- **图表**: ECharts

### 部署
- **容器**: Docker
- **编排**: Docker Compose
- **反向代理**: Nginx

## 📋 开发计划

- [x] 后端框架搭建
- [x] 数据库模型设计
- [x] API 路由实现
- [x] 前端框架搭建
- [x] 大臣管理页面
- [x] 任务管理页面
- [ ] 流转追踪页面完善
- [ ] 统计报表完善
- [ ] 配置管理完善
- [ ] OpenClaw 热重载集成
- [ ] 权限管理
- [ ] 单元测试

## 📞 联系方式

- **项目位置**: `/root/court-admin`
- **文档**: `/root/court-admin/README.md`
- **设计文档**: 飞书云文档

---

*创建时间：2026-03-10*  
*版本：v2.0.0*
