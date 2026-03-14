#!/usr/bin/env python3
"""
一次性回填脚本：将 completed 任务在 task_flows.metadata 中的 token 信息同步到 task_execution_details。

用法：
  cd /root/court-admin/backend
  PYTHONPATH=. python scripts/backfill_execution_detail_tokens.py --dry-run
  PYTHONPATH=. python scripts/backfill_execution_detail_tokens.py
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

from sqlalchemy import inspect

from app.api.tasks import TaskUpdate, _create_or_update_execution_detail, _extract_tokens_from_flow_metadata
from app.models import SessionLocal
from app.models.task import Task
from app.models.task_execution import TaskExecutionDetail


@dataclass
class BackfillStats:
    scanned: int = 0
    skipped_with_execution_tokens: int = 0
    skipped_without_flow_tokens: int = 0
    candidates: int = 0
    updated: int = 0


def _needs_backfill(detail: TaskExecutionDetail | None) -> bool:
    if detail is None:
        return True
    # total_tokens 为空即视为缺口（即使 input/output 有值，也统一回填）
    return detail.total_tokens is None


def run_backfill(dry_run: bool, limit: int | None) -> BackfillStats:
    stats = BackfillStats()
    db = SessionLocal()

    try:
        inspector = inspect(db.bind)
        required_tables = {"tasks", "task_flows", "task_execution_details"}
        if not all(inspector.has_table(name) for name in required_tables):
            print("数据库缺少必要表（tasks/task_flows/task_execution_details），请先完成迁移后再执行。")
            return stats

        query = db.query(Task).filter(Task.status == "completed").order_by(Task.id.asc())
        if limit:
            query = query.limit(limit)
        tasks = query.all()

        if not tasks:
            return stats

        detail_map = {
            row.task_id: row
            for row in db.query(TaskExecutionDetail)
            .filter(TaskExecutionDetail.task_id.in_([task.task_id for task in tasks]))
            .all()
        }

        for task in tasks:
            stats.scanned += 1
            detail = detail_map.get(task.task_id)

            if not _needs_backfill(detail):
                stats.skipped_with_execution_tokens += 1
                continue

            flow_input, flow_output, flow_total, flow_source = _extract_tokens_from_flow_metadata(task.id, db)
            if flow_input is None and flow_output is None and flow_total is None:
                stats.skipped_without_flow_tokens += 1
                continue

            stats.candidates += 1
            if dry_run:
                continue

            update_payload = TaskUpdate(
                status="completed",
                completed_at=task.completed_at,
                input_tokens=flow_input,
                output_tokens=flow_output,
                total_tokens=flow_total,
                session_key=task.agent_session_key,
                source=f"backfill:{flow_source}",
            )
            _create_or_update_execution_detail(task, update_payload, db)
            stats.updated += 1

        if not dry_run:
            db.commit()

        return stats
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="回填任务执行明细 token 缺口")
    parser.add_argument("--dry-run", action="store_true", help="仅扫描，不写入")
    parser.add_argument("--limit", type=int, default=None, help="限制扫描任务数")
    args = parser.parse_args()

    stats = run_backfill(dry_run=args.dry_run, limit=args.limit)

    print("=== task_execution_details 回填结果 ===")
    print(f"扫描 completed 任务: {stats.scanned}")
    print(f"已存在 execution detail token: {stats.skipped_with_execution_tokens}")
    print(f"flow metadata 无 token: {stats.skipped_without_flow_tokens}")
    print(f"可回填候选: {stats.candidates}")
    if args.dry_run:
        print("dry-run 模式：未写入数据库")
    else:
        print(f"实际回填: {stats.updated}")


if __name__ == "__main__":
    main()
