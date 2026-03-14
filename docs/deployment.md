# 部署指南（从零可执行）

本文按“先 OpenClaw，后 court-admin”顺序部署。

## 0. 前置要求

- Ubuntu 22.04+（或兼容 Linux）
- Node.js 18+
- Python 3.11+
- Docker + Docker Compose Plugin
- Git

安装依赖：

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates python3 python3-venv python3-pip
```

安装 Node.js（如未安装）：

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

安装 Docker（如未安装）：

```bash
sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
```

---

## 1. 安装 OpenClaw

```bash
npm install -g openclaw
openclaw --version
```

启动网关：

```bash
openclaw gateway start
openclaw gateway status
```

---

## 2. 配置 OpenClaw 六部 agents

## 2.1 准备配置文件

```bash
mkdir -p ~/.openclaw
cp -n ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.$(date +%Y%m%d-%H%M%S) 2>/dev/null || true
```

编辑配置文件（示例命令）：

```bash
vim ~/.openclaw/openclaw.json
```

必须保证 `agents.list` 中包含：
- `silijian`
- `bingbu`
- `hubu`
- `libu`
- `gongbu`
- `libu2`
- `xingbu`

并为每个 agent 配置：
- `model.primary`
- `workspace`

配置校验：

```bash
python3 -m json.tool ~/.openclaw/openclaw.json >/dev/null && echo "openclaw.json 语法正常"
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home()/'.openclaw'/'openclaw.json'
cfg = json.loads(p.read_text())
agent_ids = [a.get('id') for a in cfg.get('agents', {}).get('list', [])]
print('agents:', agent_ids)
must = {'silijian','bingbu','hubu','libu','gongbu','libu2','xingbu'}
print('missing:', sorted(must - set(agent_ids)))
PY
```

重启网关加载：

```bash
openclaw gateway restart
openclaw gateway status
```

---

## 3. 配置 Feishu 消息渠道

## 3.1 在飞书开放平台准备应用

至少准备一个机器人应用（司礼监），生产建议按六部拆分应用账号。
需要拿到：
- `appId`
- `appSecret`

## 3.2 写入 `~/.openclaw/openclaw.json`

示例结构（请替换占位符）：

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "defaultAccount": "main",
      "allowBots": true,
      "accounts": {
        "main": {
          "appId": "cli_xxx",
          "appSecret": "xxx",
          "botName": "司礼监",
          "connectionMode": "websocket",
          "domain": "feishu",
          "groupPolicy": "open",
          "dmPolicy": "pairing",
          "streaming": true,
          "requireMention": true
        }
      }
    }
  }
}
```

编辑并校验：

```bash
vim ~/.openclaw/openclaw.json
python3 -m json.tool ~/.openclaw/openclaw.json >/dev/null && echo "feishu channel config ok"
```

## 3.3 生效与验证

```bash
openclaw gateway restart
openclaw gateway status
```

验证：在目标飞书群 @机器人发送测试消息，确认可收发。

---

## 4. 部署 court-admin（Docker 推荐）

## 4.1 拉取代码

```bash
cd /root
git clone <YOUR_REPO_URL> court-admin
cd /root/court-admin
```

## 4.2 配置环境变量

```bash
cp -n .env.example .env
vim .env
```

最少要改：
- `DATABASE_URL`
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_PASSWORD`
- `CONFIG_ADMIN_TOKEN`（建议生产必填）
- `OPENCLAW_CONFIG_PATH`（通常 `~/.openclaw/openclaw.json`）

## 4.3 启动服务

```bash
docker compose up -d --build
docker compose ps
```

## 4.4 端口检查

```bash
curl -fsS http://127.0.0.1:9001/health
curl -fsS http://127.0.0.1:9001/docs >/dev/null && echo "swagger ok"
curl -I http://127.0.0.1:9002
```

---

## 5. 数据库迁移

首次部署后，执行 SQL 迁移（如存在新版本）：

```bash
cd /root/court-admin
set -a; source .env; set +a
for f in backend/sql/*.sql; do
  echo "==> apply $f"
  docker compose exec -T mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" court_admin < "$f"
done
```

> 说明：若在非 Docker MySQL 上执行，请改用本机 `mysql` 命令并指定主机/端口。

---

## 6. 本地开发部署（可选）

## 6.1 后端

```bash
cd /root/court-admin/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd /root/court-admin
cp -n .env.example .env
cd /root/court-admin/backend
uvicorn app.main:app --host 0.0.0.0 --port 9001 --reload
```

## 6.2 前端

```bash
cd /root/court-admin/frontend
npm install
npm run dev -- --host 0.0.0.0 --port 9002
```

---

## 7. 验收清单

- [ ] `openclaw gateway status` 正常
- [ ] `curl /health` 返回 `ok`
- [ ] 前端可打开并拉取 `/api/*`
- [ ] 大臣列表加载正常
- [ ] 创建任务、更新状态、查看流转正常
- [ ] 报表页能看到启用后新数据
