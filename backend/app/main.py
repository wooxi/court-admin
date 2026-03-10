"""
朝廷政务管理系统 - 后端 API 入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import ministers, tasks, flows, stats, config, models as models_api
from app.models import init_db

# 创建 FastAPI 应用
app = FastAPI(
    title="朝廷政务管理系统 API",
    description="管理 OpenClaw 六部大臣、任务流转、统计报表",
    version="2.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(ministers.router, prefix="/api/ministers", tags=["大臣管理"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务管理"])
app.include_router(flows.router, prefix="/api/flows", tags=["流转追踪"])
app.include_router(stats.router, prefix="/api/stats", tags=["统计报表"])
app.include_router(config.router, prefix="/api/config", tags=["配置管理"])
app.include_router(models_api.router, prefix="/api/models", tags=["模型管理"])

# 数据库初始化
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "message": "朝廷政务管理系统 API",
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
