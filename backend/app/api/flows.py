"""
任务流转追踪 API（兼容旧接口）
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.models import get_db
from app.models.flow import TaskFlow
from app.models.task import Task

router = APIRouter()


class FlowCreate(BaseModel):
    task_id: int
    action: str = Field(min_length=1, max_length=100)
    actor: Optional[str] = Field(default=None, min_length=1, max_length=50)
    details: Optional[dict] = None

    # 兼容旧字段
    from_actor: Optional[str] = Field(default=None, min_length=1, max_length=50)
    to_actor: Optional[str] = Field(default=None, min_length=1, max_length=50)
    remark: Optional[str] = None
    metadata: Optional[dict] = None


class FlowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    action: str
    from_actor: str
    to_actor: str
    remark: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


def _to_response(flow: TaskFlow) -> FlowResponse:
    return FlowResponse(
        id=flow.id,
        task_id=flow.task_id,
        action=flow.action,
        from_actor=flow.from_actor or "",
        to_actor=flow.to_actor or "",
        remark=flow.remark,
        metadata=flow.meta_data or {},
        created_at=flow.created_at,
    )


def _get_task_or_404(task_id: int, db: Session) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


def _normalize_payload(flow: FlowCreate) -> tuple[str, dict]:
    actor = flow.actor or flow.from_actor or "system"
    details = dict(flow.details or {})

    if flow.to_actor and "to_actor" not in details:
        details["to_actor"] = flow.to_actor
    if flow.remark and "remark" not in details:
        details["remark"] = flow.remark
    if flow.metadata:
        details["metadata"] = flow.metadata

    return actor, details


@router.get("/task/{task_id}", response_model=List[FlowResponse])
async def get_task_flows(task_id: int, db: Session = Depends(get_db)):
    _get_task_or_404(task_id, db)

    flows = (
        db.query(TaskFlow)
        .filter(TaskFlow.task_id == task_id)
        .order_by(TaskFlow.created_at.asc(), TaskFlow.id.asc())
        .all()
    )
    return [_to_response(flow) for flow in flows]


@router.post("/", response_model=FlowResponse, status_code=201)
async def create_flow(flow: FlowCreate, db: Session = Depends(get_db)):
    _get_task_or_404(flow.task_id, db)

    from_actor = flow.from_actor or flow.actor or "system"
    to_actor = flow.to_actor or "system"

    db_flow = TaskFlow(
        task_id=flow.task_id,
        from_actor=from_actor,
        to_actor=to_actor,
        action=flow.action,
        remark=flow.remark,
        meta_data=flow.metadata or {},
    )

    db.add(db_flow)
    db.commit()
    db.refresh(db_flow)
    return _to_response(db_flow)


@router.get("/timeline/{task_id}")
async def get_task_timeline(task_id: int, db: Session = Depends(get_db)):
    task = _get_task_or_404(task_id, db)

    flows = (
        db.query(TaskFlow)
        .filter(TaskFlow.task_id == task_id)
        .order_by(TaskFlow.created_at.asc(), TaskFlow.id.asc())
        .all()
    )

    total_duration = None
    if task.completed_at:
        total_duration = str(task.completed_at - task.created_at)

    return {
        "task": {
            "id": task.id,
            "task_id": task.task_id,
            "title": task.title,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
        },
        "flows": [_to_response(flow).model_dump() for flow in flows],
        "total_duration": total_duration,
    }
