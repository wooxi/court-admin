"""
数据库模型基础设施
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.settings import get_settings

settings = get_settings()

# 创建数据库引擎
engine_kwargs = {
    "pool_pre_ping": True,
    "future": True,
}

if settings.database_url.startswith("mysql"):
    engine_kwargs["connect_args"] = {
        "charset": "utf8mb4",
        "init_command": "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci",
    }

engine = create_engine(settings.database_url, **engine_kwargs)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def init_db() -> None:
    """初始化数据库表"""
    # 导入所有模型，确保 metadata 完整
    from app.models import minister, task, flow, usage, config_model  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
