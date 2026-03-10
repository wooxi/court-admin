#!/bin/bash

# 朝廷政务管理系统 - 原生启动脚本（直接运行在主机上）
# 功能：自动检测依赖、自动安装、自动建库建表、自动启动

set -e

echo "🏛️  朝廷政务管理系统启动中（原生模式）..."

# 进入项目目录
cd /root/court-admin

# 加载环境变量
if [ -f ".env" ]; then
    echo "📄 加载环境变量..."
    source .env
else
    echo "❌ .env 文件不存在，请创建配置文件"
    echo "   参考：/root/court-admin/.env.example"
    exit 1
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印函数
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# ==================== 第一步：检查并安装系统依赖 ====================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 第一步：检查并安装系统依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检测系统包管理器
if command -v apt &> /dev/null; then
    PKG_MANAGER="apt"
    UPDATE_CMD="apt update"
    INSTALL_CMD="apt install -y"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    UPDATE_CMD="yum makecache"
    INSTALL_CMD="yum install -y"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    UPDATE_CMD="dnf makecache"
    INSTALL_CMD="dnf install -y"
else
    print_error "未找到支持的包管理器（apt/yum/dnf）"
    exit 1
fi

echo "📋 检测到包管理器：$PKG_MANAGER"

# 检查并安装 Python venv
if ! python3 -m venv --help &> /dev/null; then
    print_warning "python3-venv 未安装，正在安装..."
    if [ "$PKG_MANAGER" = "apt" ]; then
        sudo $UPDATE_CMD -qq
        sudo $INSTALL_CMD python3.12-venv python3-pip > /dev/null 2>&1 || \
        sudo $INSTALL_CMD python3-venv python3-pip > /dev/null 2>&1
    else
        sudo $INSTALL_CMD python3-venv python3-pip > /dev/null 2>&1
    fi
    print_success "python3-venv 安装完成"
else
    print_success "python3-venv 已安装"
fi

# 检查并安装 MySQL 客户端
if ! command -v mysql &> /dev/null; then
    print_warning "MySQL 客户端未安装，正在安装..."
    if [ "$PKG_MANAGER" = "apt" ]; then
        sudo $UPDATE_CMD -qq
        sudo $INSTALL_CMD default-mysql-client > /dev/null 2>&1 || \
        sudo $INSTALL_CMD mysql-client > /dev/null 2>&1
    else
        sudo $INSTALL_CMD mysql > /dev/null 2>&1
    fi
    print_success "MySQL 客户端安装完成"
    MYSQL_AVAILABLE=true
else
    print_success "MySQL 客户端已安装"
    MYSQL_AVAILABLE=true
fi

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python: $PYTHON_VERSION"

# 检查 Node.js 版本
if ! command -v node &> /dev/null; then
    print_error "Node.js 未安装，请先安装 Node.js 18+"
    exit 1
fi
NODE_VERSION=$(node --version)
print_success "Node.js: $NODE_VERSION"

# ==================== 第二步：检查数据库连接 ====================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️  第二步：检查数据库连接"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

MYSQL_HOST="${MYSQL_HOST:-localhost}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_ROOT_PASSWORD:-}"
MYSQL_DATABASE="${MYSQL_DATABASE:-court_admin}"

# 测试数据库连接
echo "📋 测试数据库连接：$MYSQL_HOST:$MYSQL_PORT"

if mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "SELECT 1;" &> /dev/null; then
    print_success "数据库连接成功"
    
    # 检查数据库是否存在
    if mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "USE $MYSQL_DATABASE;" &> /dev/null; then
        print_success "数据库 $MYSQL_DATABASE 已存在"
        DATABASE_EXISTS=true
    else
        print_warning "数据库 $MYSQL_DATABASE 不存在，正在创建..."
        mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
            -e "CREATE DATABASE $MYSQL_DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        print_success "数据库创建成功"
        DATABASE_EXISTS=true
    fi
    
    # 检查表是否已存在
    TABLE_COUNT=$(mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$MYSQL_DATABASE';")
    
    if [ "$TABLE_COUNT" -gt 0 ]; then
        print_success "数据库表已存在（$TABLE_COUNT 张表）"
        TABLES_EXIST=true
    else
        print_warning "数据库表不存在，正在导入表结构..."
        mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
            "$MYSQL_DATABASE" < ./docker/mysql-init.sql
        print_success "表结构导入成功"
        TABLES_EXIST=true
    fi
else
    print_error "数据库连接失败！"
    echo ""
    echo "请检查以下配置："
    echo "  1. MySQL 服务是否启动：sudo systemctl status mysql"
    echo "  2. 数据库连接信息是否正确（编辑 .env 文件）："
    echo "     MYSQL_HOST=$MYSQL_HOST"
    echo "     MYSQL_PORT=$MYSQL_PORT"
    echo "     MYSQL_USER=$MYSQL_USER"
    echo "     MYSQL_PASSWORD=***"
    echo ""
    echo "启动 MySQL 服务："
    echo "  sudo systemctl start mysql"
    echo ""
    exit 1
fi

# ==================== 第三步：创建数据目录 ====================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 第三步：创建数据目录"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p ./data/backups
mkdir -p ./logs
print_success "数据目录创建完成"

# ==================== 第四步：安装后端依赖 ====================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 第四步：安装后端依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd /root/court-admin/backend

# 创建/检查虚拟环境
VENV_DIR="/root/court-admin/backend/venv"
VENV_ACTIVATE="$VENV_DIR/bin/activate"

if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "  创建 Python 虚拟环境..."
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
    
    # 检查是否创建成功
    if [ ! -f "$VENV_ACTIVATE" ]; then
        print_error "虚拟环境创建失败！"
        exit 1
    fi
    print_success "虚拟环境创建成功"
else
    print_success "虚拟环境已存在"
fi

# 激活虚拟环境
source "$VENV_ACTIVATE"

# 安装依赖
echo "  安装 Python 依赖包..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
print_success "后端依赖安装完成"

cd /root/court-admin

# ==================== 第五步：安装前端依赖 ====================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 第五步：安装前端依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd ./frontend

if [ ! -d "node_modules" ]; then
    echo "  安装 Node.js 依赖包..."
    npm install --silent
    print_success "前端依赖安装完成"
else
    print_success "前端依赖已安装"
fi

cd ..

# ==================== 第六步：启动服务 ====================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 第六步：启动服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 停止旧进程
echo "  检查并停止旧进程..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1

# 启动后端
echo "  启动后端服务..."

# 激活虚拟环境（使用绝对路径）
source /root/court-admin/backend/venv/bin/activate

# 设置环境变量
export DATABASE_URL="${DATABASE_URL:-mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}}"
export OPENCLAW_CONFIG_PATH="${OPENCLAW_CONFIG_PATH:-/root/.openclaw/openclaw.json}"
export BACKUP_DIR="${BACKUP_DIR:-/root/court-admin/data/backups}"

cd /root/court-admin/backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT:-9001} > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
print_success "后端已启动 (PID: $BACKEND_PID)"
cd /root/court-admin

# 等待后端启动
echo "  等待后端启动..."
sleep 5

# 检查后端是否正常启动
if curl -s http://localhost:${BACKEND_PORT:-9001}/health > /dev/null 2>&1; then
    print_success "后端服务运行正常"
else
    print_warning "后端服务可能未正常启动，请查看日志：logs/backend.log"
fi

# 启动前端
echo "  启动前端服务..."
export VITE_API_URL="${VITE_API_URL:-http://localhost:${BACKEND_PORT:-9001}}"
cd /root/court-admin/frontend
nohup npm run dev -- --port ${FRONTEND_PORT:-9002} --host > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
print_success "前端已启动 (PID: $FRONTEND_PID)"
cd /root/court-admin

# 等待前端启动
echo "  等待前端启动..."
sleep 5

# 检查前端是否正常启动
if curl -s http://localhost:${FRONTEND_PORT:-9002} > /dev/null 2>&1; then
    print_success "前端服务运行正常"
else
    print_warning "前端服务可能未正常启动，请查看日志：logs/frontend.log"
fi

# ==================== 第七步：完成 ====================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 启动完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 访问地址:"
echo "   前端：http://localhost:${FRONTEND_PORT:-9002}"
echo "   后端 API: http://localhost:${BACKEND_PORT:-9001}"
echo "   后端文档：http://localhost:${BACKEND_PORT:-9001}/docs"
echo "   健康检查：http://localhost:${BACKEND_PORT:-9001}/health"
echo "   MySQL: ${MYSQL_HOST}:${MYSQL_PORT}"
echo ""
echo "📝 进程信息:"
echo "   后端 PID: $BACKEND_PID"
echo "   前端 PID: $FRONTEND_PID"
echo ""
echo "📝 查看日志:"
echo "   后端：tail -f ${LOG_DIR:-./logs}/backend.log"
echo "   前端：tail -f ${LOG_DIR:-./logs}/frontend.log"
echo ""
echo "🛑 停止服务:"
echo "   /root/court-admin/scripts/stop-native.sh"
echo ""

# 保存 PID
echo $BACKEND_PID > ./logs/backend.pid
echo $FRONTEND_PID > ./logs/frontend.pid

# 检查总结
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 启动检查总结"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_success "Python 环境"
print_success "Node.js 环境"
print_success "MySQL 连接"
print_success "数据库和表"
print_success "后端服务"
print_success "前端服务"
echo ""
echo "🎉 所有服务启动成功！"
echo ""
