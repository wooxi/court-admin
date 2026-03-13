"""
朝廷政务管理系统 - 后端 API 入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import config, flows, ministers, models as models_api, scheduler, stats, tasks
from app.models import init_db
from app.settings import get_settings

settings = get_settings()

app = FastAPI(
    title="朝廷政务管理系统 API",
    description="管理 OpenClaw 六部大臣、任务流转、统计报表",
    version="2.1.0",
    default_response_class=JSONResponse,
)

cors_origins = settings.cors_origin_list
allow_all = "*" in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else cors_origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(ministers.router, prefix="/api/ministers", tags=["大臣管理"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务管理"])
app.include_router(flows.router, prefix="/api/flows", tags=["流转追踪"])
app.include_router(stats.router, prefix="/api/stats", tags=["统计报表"])
app.include_router(config.router, prefix="/api/config", tags=["配置管理"])
app.include_router(models_api.router, prefix="/api/models", tags=["模型管理"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["定时任务"])


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def root():
    return {
        "message": "朝廷政务管理系统 API",
        "version": "2.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
