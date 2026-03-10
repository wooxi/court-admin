# 数据模型模块
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库连接 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://court_admin:court_admin_2026@localhost:3306/court_admin"
)

# 创建数据库引擎
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

def init_db():
    """初始化数据库表"""
    # 导入所有模型
    from app.models import minister, task, flow, usage, config_model
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
