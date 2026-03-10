"""
Token 用量模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, Date
from sqlalchemy.sql import func
from app.models import Base

class TokenUsage(Base):
    __tablename__ = "token_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    minister_id = Column(Integer, ForeignKey("ministers.id"), nullable=False, index=True, comment="大臣 ID")
    task_id = Column(Integer, ForeignKey("tasks.id"), comment="任务 ID")
    input_tokens = Column(Integer, default=0, comment="输入 Token 数")
    output_tokens = Column(Integer, default=0, comment="输出 Token 数")
    total_tokens = Column(Integer, default=0, comment="总 Token 数")
    cost = Column(DECIMAL(10, 4), default=0.00, comment="成本")
    usage_date = Column("date", Date, nullable=False, comment="日期")
    created_at = Column(DateTime, default=func.now())
