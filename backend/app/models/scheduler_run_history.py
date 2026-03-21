"""
定时任务运行历史模型

用于持久化定时任务执行记录，避免仅依赖日志/缓存文件。
"""
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.models import Base


class SchedulerRunHistory(Base):
    __tablename__ = "scheduler_run_history"
    __table_args__ = (
        UniqueConstraint("task_id", "started_at", name="uk_scheduler_run_task_start"),
        {
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(128), nullable=False, index=True, comment="定时任务 ID")
    task_name = Column(String(255), nullable=True, comment="定时任务名称")

    started_at = Column(DateTime, nullable=False, index=True, comment="开始时间")
    ended_at = Column(DateTime, nullable=True, comment="结束时间")
    duration_ms = Column(Integer, nullable=True, comment="耗时（毫秒）")

    status = Column(String(32), nullable=False, default="unknown", index=True, comment="执行状态")
    result = Column(Text, nullable=True, comment="执行结果摘要")
    source = Column(String(64), nullable=False, default="scheduler_overview", comment="数据来源")
    raw_payload = Column(JSON, nullable=True, comment="原始数据快照")

    created_at = Column(DateTime, nullable=False, default=func.now(), comment="记录创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="记录更新时间")
