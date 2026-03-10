"""
任务管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models import get_db
from app.models.task import Task
from app.models.minister import Minister
from pydantic import BaseModel

router = APIRouter()

class TaskCreate(BaseModel):
    task_id: str
    title: str
    description: Optional[str] = None
    creator_id: Optional[int] = None
    assignee_id: int
    dispatcher_id: Optional[int] = None
    priority: str = "medium"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    task_id: str
    title: str
    description: Optional[str]
    assignee_id: int
    dispatcher_id: Optional[int]
    status: str
    priority: str
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str] = None,
    assignee_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取任务列表（支持筛选）"""
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    
    tasks = query.order_by(Task.created_at.desc()).limit(limit).all()
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """获取任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """创建任务"""
    # 验证大臣是否存在
    assignee = db.query(Minister).filter(Minister.id == task.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=400, detail="承办大臣不存在")
    
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    """更新任务"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    update_data = task.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    # 如果状态改为 completed，设置完成时间
    if task.status == "completed" and not db_task.completed_at:
        db_task.completed_at = datetime.now()
    
    db.commit()
    db.refresh(db_task)
    return db_task

@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    db.delete(db_task)
    db.commit()
    return {"message": "删除成功"}
