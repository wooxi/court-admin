"""
统计报表 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.sql import func as sql_func
from typing import List
from datetime import date, timedelta
from app.models import get_db
from app.models.minister import Minister
from app.models.task import Task
from app.models.usage import TokenUsage

router = APIRouter()

@router.get("/token")
async def get_token_stats(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    获取 Token 用量统计
    
    :param days: 统计天数（默认 7 天）
    """
    start_date = date.today() - timedelta(days=days)
    
    # 按大臣统计
    minister_stats = db.query(
        Minister.name,
        Minister.department,
        sql_func.sum(TokenUsage.input_tokens).label("input_tokens"),
        sql_func.sum(TokenUsage.output_tokens).label("output_tokens"),
        sql_func.sum(TokenUsage.total_tokens).label("total_tokens")
    ).join(TokenUsage).filter(
        TokenUsage.usage_date >= start_date
    ).group_by(Minister.id).all()
    
    # 总计
    total_stats = db.query(
        sql_func.sum(TokenUsage.input_tokens).label("input_tokens"),
        sql_func.sum(TokenUsage.output_tokens).label("output_tokens"),
        sql_func.sum(TokenUsage.total_tokens).label("total_tokens")
    ).filter(TokenUsage.usage_date >= start_date).first()
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": date.today().isoformat(),
            "days": days
        },
        "total": {
            "input_tokens": total_stats.input_tokens or 0,
            "output_tokens": total_stats.output_tokens or 0,
            "total_tokens": total_stats.total_tokens or 0
        },
        "by_minister": [
            {
                "name": stat.name,
                "department": stat.department,
                "input_tokens": stat.input_tokens or 0,
                "output_tokens": stat.output_tokens or 0,
                "total_tokens": stat.total_tokens or 0
            }
            for stat in minister_stats
        ]
    }

@router.get("/tasks")
async def get_task_stats(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    获取任务统计
    
    :param days: 统计天数（默认 30 天）
    """
    start_date = date.today() - timedelta(days=days)
    
    # 按大臣统计
    minister_stats = db.query(
        Minister.name,
        Minister.department,
        sql_func.count(Task.id).label("total"),
        sql_func.sum(sql_func.if_(Task.status == "completed", 1, 0)).label("completed"),
        sql_func.sum(sql_func.if_(Task.status == "processing", 1, 0)).label("processing"),
        sql_func.sum(sql_func.if_(Task.status == "pending", 1, 0)).label("pending")
    ).join(Task, Task.assignee_id == Minister.id).filter(
        Task.created_at >= start_date
    ).group_by(Minister.id).all()
    
    # 总体统计
    total_stats = db.query(
        sql_func.count(Task.id).label("total"),
        sql_func.sum(sql_func.if_(Task.status == "completed", 1, 0)).label("completed"),
        sql_func.sum(sql_func.if_(Task.status == "processing", 1, 0)).label("processing"),
        sql_func.sum(sql_func.if_(Task.status == "pending", 1, 0)).label("pending")
    ).filter(Task.created_at >= start_date).first()
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": date.today().isoformat(),
            "days": days
        },
        "total": {
            "total": total_stats.total or 0,
            "completed": total_stats.completed or 0,
            "processing": total_stats.processing or 0,
            "pending": total_stats.pending or 0,
            "completion_rate": round(
                (total_stats.completed or 0) / (total_stats.total or 1) * 100, 2
            )
        },
        "by_minister": [
            {
                "name": stat.name,
                "department": stat.department,
                "total": stat.total or 0,
                "completed": stat.completed or 0,
                "processing": stat.processing or 0,
                "pending": stat.pending or 0,
                "completion_rate": round(
                    (stat.completed or 0) / (stat.total or 1) * 100, 2
                )
            }
            for stat in minister_stats
        ]
    }

@router.get("/efficiency")
async def get_efficiency_stats(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    获取效率统计（平均处理时长）
    """
    start_date = date.today() - timedelta(days=days)
    
    # 查询已完成任务的处理时长
    completed_tasks = db.query(Task).filter(
        Task.status == "completed",
        Task.completed_at != None,
        Task.created_at >= start_date
    ).all()
    
    # 按大臣分组计算平均时长
    minister_durations = {}
    for task in completed_tasks:
        duration = (task.completed_at - task.created_at).total_seconds() / 3600  # 小时
        minister_id = task.assignee_id
        
        if minister_id not in minister_durations:
            minister_durations[minister_id] = []
        minister_durations[minister_id].append(duration)
    
    # 计算平均值
    efficiency_stats = []
    for minister_id, durations in minister_durations.items():
        minister = db.query(Minister).filter(Minister.id == minister_id).first()
        avg_duration = sum(durations) / len(durations)
        
        efficiency_stats.append({
            "minister_name": minister.name,
            "department": minister.department,
            "avg_hours": round(avg_duration, 2),
            "completed_tasks": len(durations)
        })
    
    # 按平均时长排序
    efficiency_stats.sort(key=lambda x: x["avg_hours"])
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": date.today().isoformat(),
            "days": days
        },
        "efficiency_ranking": efficiency_stats
    }
