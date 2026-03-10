"""
大臣配置模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.models import Base

class Minister(Base):
    __tablename__ = "ministers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, comment="大臣名称（如'司礼监'）")
    department = Column(String(50), nullable=False, comment="所属部门")
    model_id = Column(String(100), nullable=False, comment="模型 ID（如 bailian/qwen3.5-plus）")
    api_key = Column(String(200), comment="API Key（加密存储）")
    workspace = Column(String(500), nullable=False, comment="工作区路径")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
