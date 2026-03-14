"""
任务执行明细模型

用于记录每次任务完成时的执行指标（Token 用量、耗时等）。
仅记录功能启用后的新完成任务，不做历史回填。
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.models import Base


class TaskExecutionDetail(Base):
    __tablename__ = "task_execution_details"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), nullable=False, unique=True, index=True, comment="业务任务 ID（如 TASK-20260314-001）")
    task_pk = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True, comment="任务表主键 ID")
    minister_id = Column(Integer, ForeignKey("ministers.id"), nullable=False, index=True, comment="承办大臣 ID")

    input_tokens = Column(Integer, nullable=True, comment="输入 Token 数")
    output_tokens = Column(Integer, nullable=True, comment="输出 Token 数")
    total_tokens = Column(Integer, nullable=True, comment="总 Token 数")

    duration_seconds = Column(Integer, nullable=True, comment="任务耗时（秒）")
    completed_at = Column(DateTime, nullable=False, index=True, comment="任务完成时间")
    session_key = Column(String(128), nullable=True, index=True, comment="子会话标识")
    source = Column(String(50), nullable=False, default="task_update_api", comment="数据来源")

    created_at = Column(DateTime, nullable=False, default=func.now(), comment="记录创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="记录更新时间")
