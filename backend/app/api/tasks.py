"""
任务管理 API
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.models import get_db
from app.models.flow import TaskFlow
from app.models.minister import Minister
from app.models.task import Task
from app.models.task_execution import TaskExecutionDetail

router = APIRouter()
TaskStatus = Literal["pending", "processing", "completed"]
TaskPriority = Literal["high", "medium", "low"]


TOKEN_KEY_ALIASES = {
    "input_tokens": (
        "input_tokens",
        "inputTokens",
        "prompt_tokens",
        "promptTokens",
    ),
    "output_tokens": (
        "output_tokens",
        "outputTokens",
        "completion_tokens",
        "completionTokens",
    ),
    "total_tokens": (
        "total_tokens",
        "totalTokens",
        "tokens",
    ),
}


class TaskCreate(BaseModel):
    task_id: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    creator_id: Optional[int] = None
    assignee_id: int
    dispatcher_id: Optional[int] = None
    agent_session_key: Optional[str] = Field(default=None, max_length=128)
    status: TaskStatus = "pending"
    priority: TaskPriority = "medium"


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    agent_session_key: Optional[str] = Field(default=None, max_length=128)
    completed_at: Optional[datetime] = None

    # 任务执行明细（可选）
    input_tokens: Optional[int] = Field(default=None, ge=0)
    output_tokens: Optional[int] = Field(default=None, ge=0)
    total_tokens: Optional[int] = Field(default=None, ge=0)
    duration_seconds: Optional[int] = Field(default=None, ge=0)
    session_key: Optional[str] = Field(default=None, max_length=128)
    source: Optional[str] = Field(default=None, max_length=50)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    title: str
    description: Optional[str]
    creator_id: Optional[int]
    assignee_id: int
    dispatcher_id: Optional[int]
    agent_session_key: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    completed_at: Optional[datetime]


class TaskFlowCreate(BaseModel):
    action: str = Field(min_length=1, max_length=100)
    from_actor: str = Field(min_length=1, max_length=50)
    to_actor: str = Field(min_length=1, max_length=50)
    remark: Optional[str] = None
    meta_data: dict = Field(default_factory=dict)


class TaskFlowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    from_actor: str
    to_actor: str
    action: str
    remark: str | None = None
    metadata: dict | None = None
    created_at: datetime


def _to_flow_response(flow: TaskFlow) -> TaskFlowResponse:
    return TaskFlowResponse(
        id=flow.id,
        task_id=flow.task_id,
        from_actor=flow.from_actor or "",
        to_actor=flow.to_actor or "",
        action=flow.action,
        remark=flow.remark,
        metadata=flow.meta_data or {},
        created_at=flow.created_at,
    )


def _get_task_or_404(task_id: int, db: Session) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


def _to_int(value: Any) -> Optional[int]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return int(text)
    return None


def _find_numeric_value(payload: Any, keys: tuple[str, ...], depth: int = 0, max_depth: int = 4) -> Optional[int]:
    if depth > max_depth or not isinstance(payload, dict):
        return None

    for key in keys:
        value = _to_int(payload.get(key))
        if value is not None:
            return value

    for value in payload.values():
        if isinstance(value, dict):
            found = _find_numeric_value(value, keys, depth + 1, max_depth)
            if found is not None:
                return found

    return None


def _extract_tokens_from_flow_metadata(task_pk: int, db: Session) -> tuple[Optional[int], Optional[int], Optional[int], str]:
    flows = (
        db.query(TaskFlow)
        .filter(TaskFlow.task_id == task_pk)
        .order_by(TaskFlow.created_at.desc(), TaskFlow.id.desc())
        .limit(20)
        .all()
    )

    for flow in flows:
        metadata = flow.meta_data or {}
        if not isinstance(metadata, dict):
            continue

        input_tokens = _find_numeric_value(metadata, TOKEN_KEY_ALIASES["input_tokens"])
        output_tokens = _find_numeric_value(metadata, TOKEN_KEY_ALIASES["output_tokens"])
        total_tokens = _find_numeric_value(metadata, TOKEN_KEY_ALIASES["total_tokens"])

        if any(v is not None for v in (input_tokens, output_tokens, total_tokens)):
            if total_tokens is None and (input_tokens is not None or output_tokens is not None):
                total_tokens = (input_tokens or 0) + (output_tokens or 0)
            return input_tokens, output_tokens, total_tokens, f"task_flow:{flow.action}"

    return None, None, None, "task_update_api"


def _build_execution_payload(db_task: Task, task_update: TaskUpdate, db: Session) -> dict[str, Any]:
    input_tokens = _to_int(task_update.input_tokens)
    output_tokens = _to_int(task_update.output_tokens)
    total_tokens = _to_int(task_update.total_tokens)
    source = task_update.source or "task_update_api"

    if total_tokens is None and (input_tokens is not None or output_tokens is not None):
        total_tokens = (input_tokens or 0) + (output_tokens or 0)

    if input_tokens is None and output_tokens is None and total_tokens is None:
        flow_input, flow_output, flow_total, flow_source = _extract_tokens_from_flow_metadata(db_task.id, db)
        input_tokens = flow_input
        output_tokens = flow_output
        total_tokens = flow_total
        if not task_update.source:
            source = flow_source

    duration_seconds = _to_int(task_update.duration_seconds)
    if duration_seconds is None and db_task.completed_at and db_task.created_at:
        duration_seconds = max(int((db_task.completed_at - db_task.created_at).total_seconds()), 0)

    session_key = task_update.session_key or db_task.agent_session_key

    return {
        "task_id": db_task.task_id,
        "task_pk": db_task.id,
        "minister_id": db_task.assignee_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "duration_seconds": duration_seconds,
        "completed_at": db_task.completed_at or datetime.now(),
        "session_key": session_key,
        "source": source,
    }


def _create_or_update_execution_detail(db_task: Task, task_update: TaskUpdate, db: Session) -> None:
    payload = _build_execution_payload(db_task, task_update, db)

    existing = db.query(TaskExecutionDetail).filter(TaskExecutionDetail.task_id == db_task.task_id).first()
    if existing:
        changed = False

        for field in (
            "task_pk",
            "minister_id",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "duration_seconds",
            "completed_at",
            "session_key",
        ):
            current = getattr(existing, field)
            incoming = payload[field]
            if current is None and incoming is not None:
                setattr(existing, field, incoming)
                changed = True

        # 默认来源可被更具体来源覆盖
        if (
            payload["source"]
            and (existing.source in (None, "task_update_api"))
            and payload["source"] != existing.source
        ):
            existing.source = payload["source"]
            changed = True

        if changed:
            db.add(existing)
        return

    db.add(TaskExecutionDetail(**payload))


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[TaskStatus] = Query(default=None),
    assignee_id: Optional[int] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Task)

    if status:
        query = query.filter(Task.status == status)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)

    return query.order_by(Task.created_at.desc()).limit(limit).all()


@router.get("/by-code/{task_code}", response_model=TaskResponse)
async def get_task_by_code(task_code: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.task_id == task_code).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    return _get_task_or_404(task_id, db)


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    if db.query(Task).filter(Task.task_id == task.task_id).first():
        raise HTTPException(status_code=409, detail="任务 ID 已存在")

    assignee = db.query(Minister).filter(Minister.id == task.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=400, detail="承办大臣不存在")

    if task.dispatcher_id:
        dispatcher = db.query(Minister).filter(Minister.id == task.dispatcher_id).first()
        if not dispatcher:
            raise HTTPException(status_code=400, detail="调度大臣不存在")

    payload = task.model_dump()
    db_task = Task(**payload)
    db.add(db_task)
    db.flush()

    creator = f"minister:{task.dispatcher_id or task.creator_id}" if (task.dispatcher_id or task.creator_id) else "system"
    db.add(
        TaskFlow(
            task_id=db_task.id,
            from_actor=creator,
            to_actor=f"minister:{task.assignee_id}",
            action="task_created",
            remark="任务已创建并分派",
            meta_data={
                "task_id": db_task.task_id,
                "assignee_id": db_task.assignee_id,
                "dispatcher_id": db_task.dispatcher_id,
                "priority": db_task.priority,
                "agent_session_key": db_task.agent_session_key,
                "message": "任务已创建并分派",
            },
        )
    )

    db.commit()
    db.refresh(db_task)
    return db_task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    db_task = _get_task_or_404(task_id, db)
    update_data = task.model_dump(exclude_unset=True)

    old_status = db_task.status
    old_assignee_id = db_task.assignee_id

    if "assignee_id" in update_data and update_data["assignee_id"] is not None:
        assignee = db.query(Minister).filter(Minister.id == update_data["assignee_id"]).first()
        if not assignee:
            raise HTTPException(status_code=400, detail="承办大臣不存在")

    execution_fields = {"input_tokens", "output_tokens", "total_tokens", "duration_seconds", "session_key", "source"}

    for key, value in update_data.items():
        if key == "completed_at" or key in execution_fields:
            continue
        setattr(db_task, key, value)

    # 如果外部传了 session_key，同时补到 tasks.agent_session_key，便于后续追踪
    if task.session_key and not db_task.agent_session_key:
        db_task.agent_session_key = task.session_key

    if task.status == "completed":
        db_task.completed_at = task.completed_at or datetime.now()
    elif task.status in {"pending", "processing"}:
        db_task.completed_at = None
    elif "completed_at" in update_data:
        db_task.completed_at = update_data["completed_at"]

    if task.status and task.status != old_status:
        db.add(
            TaskFlow(
                task_id=db_task.id,
                from_actor="system",
                to_actor="system",
                action="status_changed",
                remark=f"状态变更：{old_status} → {task.status}",
                meta_data={
                    "from_status": old_status,
                    "to_status": task.status,
                    "completed_at": db_task.completed_at.isoformat() if db_task.completed_at else None,
                },
            )
        )

    if task.assignee_id and task.assignee_id != old_assignee_id:
        db.add(
            TaskFlow(
                task_id=db_task.id,
                from_actor="system",
                to_actor=f"minister:{task.assignee_id}",
                action="assignee_changed",
                remark="承办人变更",
                meta_data={
                    "from_assignee_id": old_assignee_id,
                    "to_assignee_id": task.assignee_id,
                },
            )
        )

    status_changed_to_completed = task.status == "completed" and old_status != "completed"
    if status_changed_to_completed:
        _create_or_update_execution_detail(db_task, task, db)

    db.commit()
    db.refresh(db_task)
    return db_task


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = _get_task_or_404(task_id, db)
    db.delete(db_task)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{task_id}/flows", response_model=TaskFlowResponse, status_code=201)
async def create_task_flow(task_id: int, payload: TaskFlowCreate, db: Session = Depends(get_db)):
    _get_task_or_404(task_id, db)

    db_flow = TaskFlow(
        task_id=task_id,
        from_actor=payload.from_actor,
        to_actor=payload.to_actor,
        action=payload.action,
        remark=payload.remark,
        meta_data=payload.meta_data,
    )

    db.add(db_flow)
    db.commit()
    db.refresh(db_flow)
    return _to_flow_response(db_flow)


@router.get("/{task_id}/flows", response_model=List[TaskFlowResponse])
async def get_task_flows(
    task_id: int,
    limit: int = Query(default=500, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    _get_task_or_404(task_id, db)

    flows = (
        db.query(TaskFlow)
        .filter(TaskFlow.task_id == task_id)
        .order_by(TaskFlow.created_at.asc(), TaskFlow.id.asc())
        .limit(limit)
        .all()
    )

    return [_to_flow_response(flow) for flow in flows]
