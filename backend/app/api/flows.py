"""
任务流转追踪 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models import get_db
from app.models.flow import TaskFlow
from app.models.task import Task
from pydantic import BaseModel
from typing import Optional as PydanticOptional

router = APIRouter()

class FlowCreate(BaseModel):
    task_id: int
    from_actor: str
    to_actor: str
    action: str
    remark: PydanticOptional[str] = None
    metadata: PydanticOptional[dict] = None

class FlowResponse(BaseModel):
    id: int
    task_id: int
    from_actor: str
    to_actor: str
    action: str
    remark: PydanticOptional[str]
    timestamp: datetime
    metadata: PydanticOptional[dict]
    
    class Config:
        from_attributes = True

@router.get("/task/{task_id}", response_model=List[FlowResponse])
async def get_task_flows(task_id: int, db: Session = Depends(get_db)):
    """
    获取任务完整流转链
    
    返回任务的所有流转记录，按时间排序
    """
    # 验证任务是否存在
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 获取流转记录
    flows = db.query(TaskFlow).filter(TaskFlow.task_id == task_id).order_by(TaskFlow.timestamp.asc()).all()
    return flows

@router.post("/", response_model=FlowResponse)
async def create_flow(flow: FlowCreate, db: Session = Depends(get_db)):
    """
    添加流转记录
    
    每次任务状态变更时调用
    """
    # 验证任务是否存在
    task = db.query(Task).filter(Task.id == flow.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    db_flow = TaskFlow(**flow.dict())
    db.add(db_flow)
    db.commit()
    db.refresh(db_flow)
    return db_flow

@router.get("/timeline/{task_id}")
async def get_task_timeline(task_id: int, db: Session = Depends(get_db)):
    """
    获取任务时间线（增强版）
    
    包含任务信息和完整流转链
    """
    # 获取任务
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 获取流转记录
    flows = db.query(TaskFlow).filter(TaskFlow.task_id == task_id).order_by(TaskFlow.timestamp.asc()).all()
    
    return {
        "task": {
            "id": task.id,
            "task_id": task.task_id,
            "title": task.title,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at
        },
        "flows": flows,
        "total_duration": str(task.completed_at - task.created_at) if task.completed_at else None
    }
