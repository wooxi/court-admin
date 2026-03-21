"""
统计报表 API
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, literal_column
from sqlalchemy.orm import Session

from app.models import get_db
from app.models.minister import Minister
from app.models.task import Task
from app.models.task_execution import TaskExecutionDetail
from app.models.usage import TokenUsage

router = APIRouter()


def _resolve_days_range(days: int) -> tuple[date, date]:
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    return start_date, end_date


def _resolve_datetime_window(
    days: int,
    start_time: datetime | None,
    end_time: datetime | None,
) -> tuple[datetime, datetime, str | None]:
    """解析报表时间窗口，统一返回 [start_time, end_time]。"""
    if start_time and end_time and start_time > end_time:
        return start_time, end_time, "start_time 大于 end_time"

    if start_time and end_time:
        return start_time, end_time, None

    if start_time and not end_time:
        return start_time, start_time + timedelta(days=days), None

    if end_time and not start_time:
        return end_time - timedelta(days=days), end_time, None

    start_date, end_date = _resolve_days_range(days)
    return (
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date + timedelta(days=1), datetime.min.time()) - timedelta(microseconds=1),
        None,
    )


def _serialize_execution_row(
    detail: TaskExecutionDetail,
    minister_name: str | None,
    minister_department: str | None,
    task_title: str | None,
) -> dict[str, Any]:
    return {
        "id": detail.id,
        "task_id": detail.task_id,
        "task_title": task_title,
        "task_pk": detail.task_pk,
        "assignee_id": detail.minister_id,
        "minister_id": detail.minister_id,
        "assignee_name": minister_name,
        "minister_name": minister_name,
        "department": minister_department,
        "input_tokens": detail.input_tokens,
        "output_tokens": detail.output_tokens,
        "total_tokens": detail.total_tokens,
        "duration_seconds": detail.duration_seconds,
        "completed_at": detail.completed_at,
        "session_key": detail.session_key,
        "source": detail.source,
    }


def _empty_execution_payload(
    page: int,
    page_size: int,
    filters: dict[str, Any],
    note: str,
) -> dict[str, Any]:
    return {
        "items": [],
        "summary": {
            "total_records": 0,
            "total_tokens": 0,
            "avg_tokens_per_task": 0,
            "avg_duration_seconds": 0,
            "total_duration_seconds": 0,
        },
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": 0,
            "total_pages": 0,
        },
        "filters": filters,
        "note": note,
    }


def _query_task_execution_details(
    db: Session,
    *,
    task_id: str | None,
    assignee_id: int | None,
    session_key: str | None,
    start_time: datetime | None,
    end_time: datetime | None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    filters = []
    if task_id:
        filters.append(TaskExecutionDetail.task_id == task_id)
    if assignee_id:
        filters.append(TaskExecutionDetail.minister_id == assignee_id)
    if session_key:
        filters.append(TaskExecutionDetail.session_key == session_key)
    if start_time:
        filters.append(TaskExecutionDetail.completed_at >= start_time)
    if end_time:
        filters.append(TaskExecutionDetail.completed_at <= end_time)

    filter_payload = {
        "task_id": task_id,
        "assignee_id": assignee_id,
        "session_key": session_key,
        "start_time": start_time.isoformat() if start_time else None,
        "end_time": end_time.isoformat() if end_time else None,
    }

    if start_time and end_time and start_time > end_time:
        return _empty_execution_payload(
            page=page,
            page_size=page_size,
            filters=filter_payload,
            note="start_time 大于 end_time，返回空结果。",
        )

    base_query = (
        db.query(
            TaskExecutionDetail,
            Minister.name.label("minister_name"),
            Minister.department.label("minister_department"),
            Task.title.label("task_title"),
        )
        .join(Minister, Minister.id == TaskExecutionDetail.minister_id)
        .outerjoin(Task, Task.id == TaskExecutionDetail.task_pk)
    )

    if filters:
        base_query = base_query.filter(*filters)

    total = base_query.order_by(None).count()

    aggregate_query = db.query(
        func.count(TaskExecutionDetail.id).label("total_records"),
        func.coalesce(func.sum(TaskExecutionDetail.total_tokens), 0).label("total_tokens"),
        func.coalesce(func.avg(TaskExecutionDetail.total_tokens), 0).label("avg_tokens_per_task"),
        func.coalesce(func.avg(TaskExecutionDetail.duration_seconds), 0).label("avg_duration_seconds"),
        func.coalesce(func.sum(TaskExecutionDetail.duration_seconds), 0).label("total_duration_seconds"),
    )
    if filters:
        aggregate_query = aggregate_query.filter(*filters)
    summary_row = aggregate_query.first()

    rows = (
        base_query.order_by(TaskExecutionDetail.completed_at.desc(), TaskExecutionDetail.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            _serialize_execution_row(detail, minister_name, minister_department, task_title)
            for detail, minister_name, minister_department, task_title in rows
        ],
        "summary": {
            "total_records": int(summary_row.total_records or 0),
            "total_tokens": int(summary_row.total_tokens or 0),
            "avg_tokens_per_task": round(float(summary_row.avg_tokens_per_task or 0), 2),
            "avg_duration_seconds": round(float(summary_row.avg_duration_seconds or 0), 2),
            "total_duration_seconds": int(summary_row.total_duration_seconds or 0),
        },
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": int(total or 0),
            "total_pages": (int(total or 0) + page_size - 1) // page_size if total else 0,
        },
        "filters": filter_payload,
        "note": "统一 token 口径：数据来源 task_execution_details，仅统计明细功能启用后的新完成任务。",
    }


@router.get("/token")
async def get_token_stats(
    days: int = Query(default=7, ge=1, le=365),
    db: Session = Depends(get_db),
):
    start_date, end_date = _resolve_days_range(days)

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
            "end": end_date.isoformat(),
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
    start_date, end_date = _resolve_days_range(days)

    completed_case = case((Task.status == "completed", 1), else_=0)
    processing_case = case((Task.status == "processing", 1), else_=0)
    pending_case = case((Task.status == "pending", 1), else_=0)

    minister_stats = (
        db.query(
            Minister.id,
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
            "end": end_date.isoformat(),
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
                "id": int(stat.id),
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
    start_date, end_date = _resolve_days_range(days)

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
            "end": end_date.isoformat(),
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


@router.get("/task-executions/trend")
async def get_task_execution_trend(
    days: int = Query(default=7, ge=7, le=30),
    minister_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
):
    """
    按天聚合任务执行趋势（仅统计启用后新增数据）。

    - 支持 7 天 / 30 天窗口
    - 支持按大臣筛选
    - 指标：每日 token 总量、每日总耗时、每日平均耗时、任务数
    """
    start_date, end_date = _resolve_days_range(days)
    start_time = datetime.combine(start_date, datetime.min.time())
    end_time = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

    filters = [
        TaskExecutionDetail.completed_at >= start_time,
        TaskExecutionDetail.completed_at < end_time,
    ]
    if minister_id:
        filters.append(TaskExecutionDetail.minister_id == minister_id)

    day_expr = func.date(TaskExecutionDetail.completed_at)
    rows = (
        db.query(
            day_expr.label("day"),
            func.count(TaskExecutionDetail.id).label("task_count"),
            func.coalesce(func.sum(TaskExecutionDetail.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(TaskExecutionDetail.duration_seconds), 0).label("total_duration_seconds"),
            func.coalesce(func.avg(TaskExecutionDetail.duration_seconds), 0).label("avg_duration_seconds"),
        )
        .filter(*filters)
        .group_by(day_expr)
        .order_by(day_expr.asc())
        .all()
    )

    row_map: dict[str, object] = {}
    for row in rows:
        day_key = row.day.isoformat() if hasattr(row.day, "isoformat") else str(row.day)
        row_map[day_key] = row

    trend = []
    cursor = start_date
    while cursor <= end_date:
        key = cursor.isoformat()
        row = row_map.get(key)

        if row:
            task_count = int(getattr(row, "task_count", 0) or 0)
            total_tokens = int(getattr(row, "total_tokens", 0) or 0)
            total_duration_seconds = int(getattr(row, "total_duration_seconds", 0) or 0)
            avg_duration_seconds = round(float(getattr(row, "avg_duration_seconds", 0) or 0), 2)
        else:
            task_count = 0
            total_tokens = 0
            total_duration_seconds = 0
            avg_duration_seconds = 0

        trend.append(
            {
                "date": key,
                "task_count": task_count,
                "total_tokens": total_tokens,
                "total_duration_seconds": total_duration_seconds,
                "avg_duration_seconds": avg_duration_seconds,
            }
        )

        cursor += timedelta(days=1)

    minister = None
    if minister_id:
        minister_row = db.query(Minister.id, Minister.name, Minister.department).filter(Minister.id == minister_id).first()
        if minister_row:
            minister = {
                "id": minister_row.id,
                "name": minister_row.name,
                "department": minister_row.department,
            }

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days,
        },
        "filters": {
            "minister_id": minister_id,
            "minister": minister,
        },
        "trend": trend,
        "note": "仅统计任务执行明细功能启用后产生的新完成任务数据，不回填历史任务。",
    }


@router.get("/task-executions/details")
async def get_task_execution_details_v2(
    task_id: str | None = Query(default=None),
    assignee_id: int | None = Query(default=None, ge=1),
    session_key: str | None = Query(default=None),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    任务执行明细（统一 token 口径）。

    基于 task_execution_details，支持以下筛选：
    - task_id
    - assignee_id
    - session_key
    - start_time / end_time
    - page / page_size
    """
    return _query_task_execution_details(
        db,
        task_id=task_id,
        assignee_id=assignee_id,
        session_key=session_key,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )


@router.get("/task-executions")
async def get_task_execution_details(
    minister_id: int | None = Query(default=None, ge=1),
    task_id: str | None = Query(default=None),
    session_key: str | None = Query(default=None),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    任务执行明细（兼容旧接口）。

    - minister_id 作为 assignee_id 别名
    - 新增支持 task_id / session_key 筛选
    """
    payload = _query_task_execution_details(
        db,
        task_id=task_id,
        assignee_id=minister_id,
        session_key=session_key,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )
    payload.setdefault("filters", {})
    payload["filters"]["minister_id"] = minister_id
    return payload


@router.get("/task-executions/report")
async def get_task_execution_report(
    days: int = Query(default=7, ge=1, le=365),
    assignee_id: int | None = Query(default=None, ge=1),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    执行报表聚合接口（单接口返回）：
    - kpi
    - daily_trend
    - dept_distribution
    - status_distribution
    """
    window_start, window_end, err = _resolve_datetime_window(days=days, start_time=start_time, end_time=end_time)
    if err:
        return {
            "period": {
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "days": days,
            },
            "filters": {
                "assignee_id": assignee_id,
            },
            "kpi": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "completion_rate": 0,
                "execution_records": 0,
                "total_tokens": 0,
                "avg_tokens_per_task": 0,
                "total_duration_seconds": 0,
                "avg_duration_seconds": 0,
            },
            "daily_trend": [],
            "dept_distribution": [],
            "status_distribution": [],
            "note": err,
        }

    detail_filters = [
        TaskExecutionDetail.completed_at >= window_start,
        TaskExecutionDetail.completed_at <= window_end,
    ]
    task_filters = [
        Task.created_at >= window_start,
        Task.created_at <= window_end,
    ]

    if assignee_id:
        detail_filters.append(TaskExecutionDetail.minister_id == assignee_id)
        task_filters.append(Task.assignee_id == assignee_id)

    # KPI
    task_total_row = (
        db.query(
            func.count(Task.id).label("total_tasks"),
            func.coalesce(func.sum(case((Task.status == "completed", 1), else_=0)), 0).label("completed_tasks"),
        )
        .filter(*task_filters)
        .first()
    )

    detail_total_row = (
        db.query(
            func.count(TaskExecutionDetail.id).label("execution_records"),
            func.coalesce(func.sum(TaskExecutionDetail.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.avg(TaskExecutionDetail.total_tokens), 0).label("avg_tokens_per_task"),
            func.coalesce(func.sum(TaskExecutionDetail.duration_seconds), 0).label("total_duration_seconds"),
            func.coalesce(func.avg(TaskExecutionDetail.duration_seconds), 0).label("avg_duration_seconds"),
        )
        .filter(*detail_filters)
        .first()
    )

    total_tasks = int(task_total_row.total_tasks or 0)
    completed_tasks = int(task_total_row.completed_tasks or 0)

    # Daily trend
    day_expr = func.date(TaskExecutionDetail.completed_at)
    trend_rows = (
        db.query(
            day_expr.label("day"),
            func.count(TaskExecutionDetail.id).label("task_count"),
            func.coalesce(func.sum(TaskExecutionDetail.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.avg(TaskExecutionDetail.total_tokens), 0).label("avg_tokens_per_task"),
            func.coalesce(func.sum(TaskExecutionDetail.duration_seconds), 0).label("total_duration_seconds"),
            func.coalesce(func.avg(TaskExecutionDetail.duration_seconds), 0).label("avg_duration_seconds"),
        )
        .filter(*detail_filters)
        .group_by(day_expr)
        .order_by(day_expr.asc())
        .all()
    )

    trend_row_map: dict[str, Any] = {}
    for row in trend_rows:
        day_key = row.day.isoformat() if hasattr(row.day, "isoformat") else str(row.day)
        trend_row_map[day_key] = row

    daily_trend: list[dict[str, Any]] = []
    cursor = window_start.date()
    end_date = window_end.date()
    while cursor <= end_date:
        key = cursor.isoformat()
        row = trend_row_map.get(key)
        if row:
            daily_trend.append(
                {
                    "date": key,
                    "task_count": int(row.task_count or 0),
                    "total_tokens": int(row.total_tokens or 0),
                    "avg_tokens_per_task": round(float(row.avg_tokens_per_task or 0), 2),
                    "total_duration_seconds": int(row.total_duration_seconds or 0),
                    "avg_duration_seconds": round(float(row.avg_duration_seconds or 0), 2),
                }
            )
        else:
            daily_trend.append(
                {
                    "date": key,
                    "task_count": 0,
                    "total_tokens": 0,
                    "avg_tokens_per_task": 0,
                    "total_duration_seconds": 0,
                    "avg_duration_seconds": 0,
                }
            )
        cursor += timedelta(days=1)

    # 部门分布（按执行明细）
    dept_rows = (
        db.query(
            Minister.department.label("department"),
            func.count(TaskExecutionDetail.id).label("task_count"),
            func.coalesce(func.sum(TaskExecutionDetail.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.avg(TaskExecutionDetail.total_tokens), 0).label("avg_tokens_per_task"),
            func.coalesce(func.sum(TaskExecutionDetail.duration_seconds), 0).label("total_duration_seconds"),
        )
        .join(Minister, Minister.id == TaskExecutionDetail.minister_id)
        .filter(*detail_filters)
        .group_by(Minister.department)
        .order_by(func.coalesce(func.sum(TaskExecutionDetail.total_tokens), 0).desc(), Minister.department.asc())
        .all()
    )

    # 状态分布（按任务表）
    status_rows = (
        db.query(
            Task.status.label("status"),
            func.count(Task.id).label("count"),
        )
        .filter(*task_filters)
        .group_by(Task.status)
        .all()
    )
    status_map: dict[str, int] = {
        "pending": 0,
        "processing": 0,
        "completed": 0,
    }
    for row in status_rows:
        status_map[str(row.status)] = int(row.count or 0)

    return {
        "period": {
            "start_time": window_start.isoformat(),
            "end_time": window_end.isoformat(),
            "days": days,
        },
        "filters": {
            "assignee_id": assignee_id,
        },
        "kpi": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round((completed_tasks / total_tasks * 100), 2) if total_tasks else 0,
            "execution_records": int(detail_total_row.execution_records or 0),
            "total_tokens": int(detail_total_row.total_tokens or 0),
            "avg_tokens_per_task": round(float(detail_total_row.avg_tokens_per_task or 0), 2),
            "total_duration_seconds": int(detail_total_row.total_duration_seconds or 0),
            "avg_duration_seconds": round(float(detail_total_row.avg_duration_seconds or 0), 2),
        },
        "daily_trend": daily_trend,
        "dept_distribution": [
            {
                "department": row.department,
                "task_count": int(row.task_count or 0),
                "total_tokens": int(row.total_tokens or 0),
                "avg_tokens_per_task": round(float(row.avg_tokens_per_task or 0), 2),
                "total_duration_seconds": int(row.total_duration_seconds or 0),
            }
            for row in dept_rows
        ],
        "status_distribution": [
            {
                "status": key,
                "count": value,
            }
            for key, value in status_map.items()
        ],
        "note": "统一口径：token 与耗时统计基于 task_execution_details，状态统计基于 tasks。",
    }
