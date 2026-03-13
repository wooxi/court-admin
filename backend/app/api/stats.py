"""
统计报表 API
"""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, literal_column
from sqlalchemy.orm import Session

from app.models import get_db
from app.models.minister import Minister
from app.models.task import Task
from app.models.usage import TokenUsage

router = APIRouter()


@router.get("/token")
async def get_token_stats(
    days: int = Query(default=7, ge=1, le=365),
    db: Session = Depends(get_db),
):
    start_date = date.today() - timedelta(days=days)

    minister_stats = (
        db.query(
            Minister.name,
            Minister.department,
            func.coalesce(func.sum(TokenUsage.input_tokens), 0).label("input_tokens"),
            func.coalesce(func.sum(TokenUsage.output_tokens), 0).label("output_tokens"),
            func.coalesce(func.sum(TokenUsage.total_tokens), 0).label("total_tokens"),
        )
        .outerjoin(
            TokenUsage,
            (TokenUsage.minister_id == Minister.id) & (TokenUsage.usage_date >= start_date),
        )
        .group_by(Minister.id, Minister.name, Minister.department)
        .order_by(Minister.id.asc())
        .all()
    )

    total_stats = (
        db.query(
            func.coalesce(func.sum(TokenUsage.input_tokens), 0).label("input_tokens"),
            func.coalesce(func.sum(TokenUsage.output_tokens), 0).label("output_tokens"),
            func.coalesce(func.sum(TokenUsage.total_tokens), 0).label("total_tokens"),
        )
        .filter(TokenUsage.usage_date >= start_date)
        .first()
    )

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": date.today().isoformat(),
            "days": days,
        },
        "total": {
            "input_tokens": int(total_stats.input_tokens or 0),
            "output_tokens": int(total_stats.output_tokens or 0),
            "total_tokens": int(total_stats.total_tokens or 0),
        },
        "by_minister": [
            {
                "name": stat.name,
                "department": stat.department,
                "input_tokens": int(stat.input_tokens or 0),
                "output_tokens": int(stat.output_tokens or 0),
                "total_tokens": int(stat.total_tokens or 0),
            }
            for stat in minister_stats
        ],
    }


@router.get("/tasks")
async def get_task_stats(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    start_date = date.today() - timedelta(days=days)

    completed_case = case((Task.status == "completed", 1), else_=0)
    processing_case = case((Task.status == "processing", 1), else_=0)
    pending_case = case((Task.status == "pending", 1), else_=0)

    minister_stats = (
        db.query(
            Minister.name,
            Minister.department,
            func.count(Task.id).label("total"),
            func.coalesce(func.sum(completed_case), 0).label("completed"),
            func.coalesce(func.sum(processing_case), 0).label("processing"),
            func.coalesce(func.sum(pending_case), 0).label("pending"),
        )
        .outerjoin(Task, (Task.assignee_id == Minister.id) & (Task.created_at >= start_date))
        .group_by(Minister.id, Minister.name, Minister.department)
        .order_by(Minister.id.asc())
        .all()
    )

    total_stats = (
        db.query(
            func.count(Task.id).label("total"),
            func.coalesce(func.sum(completed_case), 0).label("completed"),
            func.coalesce(func.sum(processing_case), 0).label("processing"),
            func.coalesce(func.sum(pending_case), 0).label("pending"),
        )
        .filter(Task.created_at >= start_date)
        .first()
    )

    total = int(total_stats.total or 0)
    completed = int(total_stats.completed or 0)

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": date.today().isoformat(),
            "days": days,
        },
        "total": {
            "total": total,
            "completed": completed,
            "processing": int(total_stats.processing or 0),
            "pending": int(total_stats.pending or 0),
            "completion_rate": round((completed / total * 100), 2) if total else 0,
        },
        "by_minister": [
            {
                "name": stat.name,
                "department": stat.department,
                "total": int(stat.total or 0),
                "completed": int(stat.completed or 0),
                "processing": int(stat.processing or 0),
                "pending": int(stat.pending or 0),
                "completion_rate": round((int(stat.completed or 0) / int(stat.total or 0) * 100), 2)
                if int(stat.total or 0)
                else 0,
            }
            for stat in minister_stats
        ],
    }


@router.get("/efficiency")
async def get_efficiency_stats(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    start_date = date.today() - timedelta(days=days)

    # 按大臣统计已完成任务平均耗时（小时）
    # 这里 SECOND 需作为 SQL 关键字字面量，不能做绑定参数
    seconds_diff = func.timestampdiff(literal_column("SECOND"), Task.created_at, Task.completed_at)
    avg_hours = func.avg(seconds_diff / 3600.0)

    rows = (
        db.query(
            Minister.id,
            Minister.name,
            Minister.department,
            func.coalesce(avg_hours, 0).label("avg_hours"),
            func.count(Task.id).label("completed_tasks"),
        )
        .join(Task, Task.assignee_id == Minister.id)
        .filter(
            Task.status == "completed",
            Task.completed_at.isnot(None),
            Task.created_at >= start_date,
        )
        .group_by(Minister.id, Minister.name, Minister.department)
        .order_by(func.coalesce(avg_hours, 0).asc())
        .all()
    )

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": date.today().isoformat(),
            "days": days,
        },
        "efficiency_ranking": [
            {
                "minister_id": row.id,
                "minister_name": row.name,
                "department": row.department,
                "avg_hours": round(float(row.avg_hours or 0), 2),
                "completed_tasks": int(row.completed_tasks or 0),
            }
            for row in rows
        ],
    }
