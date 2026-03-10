"""
任务模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models import Base

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, nullable=False, index=True, comment="任务 ID（如 JJC-20260310-001）")
    title = Column(String(500), nullable=False, comment="任务标题")
    description = Column(Text, comment="任务描述")
    creator_id = Column(Integer, ForeignKey("ministers.id"), comment="创建人 ID")
    assignee_id = Column(Integer, ForeignKey("ministers.id"), nullable=False, comment="承办大臣 ID")
    dispatcher_id = Column(Integer, ForeignKey("ministers.id"), comment="调度大臣 ID（司礼监）")
    status = Column(String(20), nullable=False, default="pending", comment="状态：pending/processing/completed")
    priority = Column(String(10), default="medium", comment="优先级：high/medium/low")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 关系
    assignee = relationship("Minister", foreign_keys=[assignee_id])
    dispatcher = relationship("Minister", foreign_keys=[dispatcher_id])
