"""
任务流转模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from app.models import Base

class TaskFlow(Base):
    __tablename__ = "task_flows"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True, comment="任务 ID")
    from_actor = Column(String(50), nullable=False, comment="发起方")
    to_actor = Column(String(50), nullable=False, comment="接收方")
    action = Column(String(100), nullable=False, comment="动作类型")
    remark = Column(Text, comment="备注")
    timestamp = Column(DateTime, nullable=False, default=func.now(), comment="时间戳")
    flow_metadata = Column("metadata", MySQLJSON, comment="扩展元数据")
    created_at = Column(DateTime, default=func.now())
