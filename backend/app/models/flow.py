"""
任务流转模型
"""
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.models import Base


class TaskFlow(Base):
    __tablename__ = "task_flows"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True, comment="任务 ID")
    from_actor = Column(String(50), nullable=False, comment="发起方")
    to_actor = Column(String(50), nullable=False, comment="接收方")
    action = Column(String(100), nullable=False, comment="动作类型")
    remark = Column(String, nullable=True, comment="备注")
    meta_data = Column("metadata", JSON, nullable=True, comment="扩展元数据")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="记录时间")
