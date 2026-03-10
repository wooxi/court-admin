"""
OpenClaw 配置模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.models import Base

class OpenClawConfig(Base):
    __tablename__ = "openclaw_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True, comment="配置键")
    config_value = Column(Text, nullable=False, comment="配置值（JSON）")
    version = Column(String(20), nullable=False, comment="版本号")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    updated_by = Column(String(50), comment="更新人")
