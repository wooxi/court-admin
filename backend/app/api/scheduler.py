"""
定时任务总览 API
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models import get_db
from app.models.scheduler_run_history import SchedulerRunHistory
from app.settings import get_settings

router = APIRouter()
settings = get_settings()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOG_LINE_RE = re.compile(r"^\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s*\[(?P<level>[A-Z]+)\]\s*(?P<msg>.*)$")

SCHEDULE_KEYWORDS = {
    "cron",
    "schedule",
    "schedules",
    "heartbeat",
    "heartbeats",
    "timer",
    "timers",
    "job",
    "jobs",
    "interval",
}

SCHEDULE_FIELDS = (
    "schedule",
    "cron",
    "cron_expr",
    "cron_expression",
    "expression",
    "interval",
    "every",
)

RUN_START_KEYS = (
    "started_at",
    "start_time",
    "startedAt",
    "startAt",
    "timestamp",
)
RUN_END_KEYS = ("ended_at", "end_time", "finished_at", "endedAt", "endAt")
RUN_STATUS_KEYS = ("status", "last_status", "state", "result_status")
RUN_RESULT_KEYS = ("result", "last_result", "message", "output", "summary")


class SchedulerTaskItem(BaseModel):
    id: str
    name: str
    schedule: str
    enabled: bool = True
    source: str
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    last_status: Optional[str] = None
    last_result: Optional[str] = None


class SchedulerRunItem(BaseModel):
    task_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str = "unknown"
    result: Optional[str] = None
    source: Optional[str] = None


class SchedulerOverviewResponse(BaseModel):
    ok: bool = True
    generated_at: datetime
    tasks: List[SchedulerTaskItem] = Field(default_factory=list)
    runs: List[SchedulerRunItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


def _build_scheduler_overview(db: Session) -> SchedulerOverviewResponse:
    warnings: List[str] = []
    errors: List[str] = []

    tasks_map: Dict[str, SchedulerTaskItem] = {}
    runs: List[SchedulerRunItem] = []

    try:
        config = _safe_load_openclaw_config(warnings=warnings, errors=errors)
        if config:
            config_tasks = _extract_tasks_from_openclaw_config(config)
            for task in config_tasks:
                _merge_task(tasks_map, task)

        cache_tasks, cache_runs = _load_cached_scheduler_data(warnings=warnings, errors=errors)
        for task in cache_tasks:
            _merge_task(tasks_map, task)
        runs.extend(cache_runs)

        log_tasks, log_runs = _build_tasks_and_runs_from_logs(warnings=warnings)
        for task in log_tasks:
            _merge_task(tasks_map, task)
        runs.extend(log_runs)

        # 合并 run 信息到 task 摘要字段
        _attach_run_summary(tasks_map, runs)

        persist_result = _persist_scheduler_runs(db, runs, tasks_map)
        if persist_result["inserted"] or persist_result["updated"]:
            warnings.append(
                f"scheduler_run_history 已同步：新增 {persist_result['inserted']}，更新 {persist_result['updated']}"
            )

        all_tasks = sorted(tasks_map.values(), key=lambda x: x.id)
        all_runs = sorted(runs, key=lambda x: x.started_at, reverse=True)[:200]

        return SchedulerOverviewResponse(
            ok=(len(errors) == 0),
            generated_at=datetime.utcnow(),
            tasks=all_tasks,
            runs=all_runs,
            warnings=warnings,
            errors=errors,
        )
    except Exception as e:  # noqa: BLE001 - 对外返回可读错误，避免裸 500
        db.rollback()
        errors.append(f"构建定时任务总览失败：{e}")
        return SchedulerOverviewResponse(
            ok=False,
            generated_at=datetime.utcnow(),
            tasks=sorted(tasks_map.values(), key=lambda x: x.id),
            runs=sorted(runs, key=lambda x: x.started_at, reverse=True)[:200],
            warnings=warnings,
            errors=errors,
        )


@router.get("/overview", response_model=SchedulerOverviewResponse)
async def get_scheduler_overview(db: Session = Depends(get_db)):
    return _build_scheduler_overview(db)


@router.get('/jobs')
async def list_scheduler_jobs(db: Session = Depends(get_db)):
    overview = _build_scheduler_overview(db)
    return overview.tasks


@router.get('/tasks')
async def list_scheduler_tasks(db: Session = Depends(get_db)):
    """/tasks 作为 /jobs 别名，兼容不同前端调用。"""
    overview = _build_scheduler_overview(db)
    return overview.tasks


@router.get('/runs')
async def list_scheduler_runs(
    limit: int = Query(default=20, ge=1, le=200),
    task_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    overview = _build_scheduler_overview(db)
    runs = overview.runs
    if task_id:
        runs = [item for item in runs if item.task_id == task_id]
    return runs[:limit]


@router.get('/run-history')
async def list_scheduler_run_history(
    task_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    start_time: Optional[datetime] = Query(default=None),
    end_time: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if start_time and end_time and start_time > end_time:
        return {
            "items": [],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": 0,
                "total_pages": 0,
            },
            "filters": {
                "task_id": task_id,
                "status": status,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            "note": "start_time 大于 end_time，返回空结果。",
        }

    query = db.query(SchedulerRunHistory)
    if task_id:
        query = query.filter(SchedulerRunHistory.task_id == task_id)
    if status:
        query = query.filter(SchedulerRunHistory.status == status)
    if start_time:
        query = query.filter(SchedulerRunHistory.started_at >= start_time)
    if end_time:
        query = query.filter(SchedulerRunHistory.started_at <= end_time)

    total = query.order_by(None).count()
    rows = (
        query.order_by(SchedulerRunHistory.started_at.desc(), SchedulerRunHistory.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            {
                "id": row.id,
                "task_id": row.task_id,
                "task_name": row.task_name,
                "started_at": row.started_at,
                "ended_at": row.ended_at,
                "duration_ms": row.duration_ms,
                "status": row.status,
                "result": row.result,
                "source": row.source,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
            for row in rows
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": int(total or 0),
            "total_pages": (int(total or 0) + page_size - 1) // page_size if total else 0,
        },
        "filters": {
            "task_id": task_id,
            "status": status,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
        },
    }


@router.get('/jobs/{job_id}')
async def get_scheduler_job(job_id: str, db: Session = Depends(get_db)):
    overview = _build_scheduler_overview(db)
    task = next((item for item in overview.tasks if item.id == job_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail=f'任务不存在：{job_id}')
    return task


@router.get('/jobs/{job_id}/runs')
async def get_scheduler_job_runs(
    job_id: str,
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    overview = _build_scheduler_overview(db)
    runs = [item for item in overview.runs if item.task_id == job_id]
    return runs[:limit]


def _run_source_priority(source: str | None) -> int:
    if not source:
        return 0
    if source.startswith("logs"):
        return 30
    if source.startswith("cache"):
        return 20
    if source.startswith("openclaw_config"):
        return 10
    return 0


def _deduplicate_runs(runs: List[SchedulerRunItem]) -> List[SchedulerRunItem]:
    """按 task_id + started_at 去重，优先保留来源更可靠/状态更明确的记录。"""
    sorted_runs = sorted(
        runs,
        key=lambda item: (
            item.started_at,
            _run_source_priority(item.source),
            1 if item.status and item.status != "unknown" else 0,
        ),
        reverse=True,
    )

    dedup: Dict[Tuple[str, datetime], SchedulerRunItem] = {}
    for run in sorted_runs:
        key = (run.task_id, run.started_at)
        if key not in dedup:
            dedup[key] = run

    return list(dedup.values())


def _persist_scheduler_runs(
    db: Session,
    runs: List[SchedulerRunItem],
    tasks_map: Dict[str, SchedulerTaskItem],
) -> Dict[str, int]:
    normalized_runs = _deduplicate_runs(runs)
    if not normalized_runs:
        return {"inserted": 0, "updated": 0}

    task_ids = {run.task_id for run in normalized_runs}
    min_started_at = min(run.started_at for run in normalized_runs)
    max_started_at = max(run.started_at for run in normalized_runs)

    existing_rows = (
        db.query(SchedulerRunHistory)
        .filter(
            SchedulerRunHistory.task_id.in_(task_ids),
            SchedulerRunHistory.started_at >= min_started_at,
            SchedulerRunHistory.started_at <= max_started_at,
        )
        .all()
    )
    existing_map = {(row.task_id, row.started_at): row for row in existing_rows}

    inserted = 0
    updated = 0

    for run in normalized_runs:
        key = (run.task_id, run.started_at)
        task_name = tasks_map.get(run.task_id).name if tasks_map.get(run.task_id) else run.task_id
        payload = {
            "task_id": run.task_id,
            "task_name": task_name,
            "started_at": run.started_at,
            "ended_at": run.ended_at,
            "duration_ms": run.duration_ms,
            "status": run.status or "unknown",
            "result": run.result,
            "source": run.source or "scheduler_overview",
            "raw_payload": {
                "task_id": run.task_id,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "ended_at": run.ended_at.isoformat() if run.ended_at else None,
                "duration_ms": run.duration_ms,
                "status": run.status,
                "result": run.result,
                "source": run.source,
            },
        }

        existing = existing_map.get(key)
        if existing:
            changed = False
            for field in ("task_name", "ended_at", "duration_ms", "status", "result", "source", "raw_payload"):
                incoming = payload[field]
                if incoming is None:
                    continue
                if getattr(existing, field) != incoming:
                    setattr(existing, field, incoming)
                    changed = True
            if changed:
                db.add(existing)
                updated += 1
            continue

        db.add(SchedulerRunHistory(**payload))
        inserted += 1

    if inserted or updated:
        db.commit()

    return {"inserted": inserted, "updated": updated}


def _safe_load_openclaw_config(*, warnings: List[str], errors: List[str]) -> Optional[Dict[str, Any]]:
    path = settings.openclaw_config_path
    if not path.exists():
        warnings.append(f"OpenClaw 配置文件不存在：{path}")
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            warnings.append("OpenClaw 配置根节点不是对象，已跳过配置提取")
            return None
        return data
    except json.JSONDecodeError as e:
        errors.append(f"OpenClaw 配置解析失败：{e}")
        return None
    except OSError as e:
        errors.append(f"读取 OpenClaw 配置失败：{e}")
        return None


def _extract_tasks_from_openclaw_config(config: Dict[str, Any]) -> List[SchedulerTaskItem]:
    tasks: List[SchedulerTaskItem] = []
    seen: set[Tuple[str, str]] = set()

    for path, node in _walk_dict_nodes(config):
        path_text = ".".join(path)
        lower_path = path_text.lower()
        path_hint = any(word in lower_path for word in SCHEDULE_KEYWORDS)

        schedule_val = _pick_first(node, SCHEDULE_FIELDS)
        if schedule_val is None and not path_hint:
            continue

        task_id = _as_str(_pick_first(node, ("id", "task_id", "job_id", "name", "key")))
        if not task_id:
            task_id = f"cfg:{path[-1]}" if path else "cfg:task"

        name = _as_str(_pick_first(node, ("name", "title", "task", "job", "description"))) or task_id

        schedule = _normalize_schedule(schedule_val)
        if not schedule:
            interval_hint = _pick_first(node, ("interval", "every"))
            schedule = _normalize_schedule(interval_hint) or "unknown"

        enabled_raw = _pick_first(node, ("enabled", "active", "is_enabled", "is_active"))
        enabled = True if enabled_raw is None else bool(enabled_raw)

        next_run = _parse_datetime(_pick_first(node, ("next_run", "nextRun", "next_at", "nextAt")))
        last_run = _parse_datetime(_pick_first(node, ("last_run", "lastRun", "last_at", "lastAt")))

        last_status = _as_str(_pick_first(node, RUN_STATUS_KEYS))
        last_result = _as_str(_pick_first(node, RUN_RESULT_KEYS))

        source = f"openclaw_config:{path_text or 'root'}"
        dedup_key = (task_id, source)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        tasks.append(
            SchedulerTaskItem(
                id=task_id,
                name=name,
                schedule=schedule,
                enabled=enabled,
                source=source,
                next_run=next_run,
                last_run=last_run,
                last_status=last_status,
                last_result=last_result,
            )
        )

    return tasks


def _walk_dict_nodes(value: Any, path: Optional[List[str]] = None) -> Iterable[Tuple[List[str], Dict[str, Any]]]:
    if path is None:
        path = []

    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from _walk_dict_nodes(child, path + [str(key)])
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            yield from _walk_dict_nodes(child, path + [str(idx)])


def _load_cached_scheduler_data(*, warnings: List[str], errors: List[str]) -> Tuple[List[SchedulerTaskItem], List[SchedulerRunItem]]:
    tasks: List[SchedulerTaskItem] = []
    runs: List[SchedulerRunItem] = []

    candidate_files = [
        PROJECT_ROOT / "data" / "scheduler_overview_cache.json",
        PROJECT_ROOT / "data" / "scheduler_runs.json",
        PROJECT_ROOT / "data" / "cron_runs.json",
        PROJECT_ROOT / "logs" / "scheduler_runs.jsonl",
        PROJECT_ROOT / "logs" / "cron_runs.jsonl",
    ]

    for file_path in candidate_files:
        if not file_path.exists():
            continue

        source = str(file_path.relative_to(PROJECT_ROOT))
        try:
            if file_path.suffix == ".jsonl":
                file_runs = _load_runs_from_jsonl(file_path)
                for run in file_runs:
                    parsed = _mapping_to_run(run, source=f"cache:{source}")
                    if parsed:
                        runs.append(parsed)
                continue

            raw = json.loads(file_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for item in raw.get("tasks", []) or []:
                    parsed_task = _mapping_to_task(item, source=f"cache:{source}")
                    if parsed_task:
                        tasks.append(parsed_task)

                for item in raw.get("runs", []) or []:
                    parsed_run = _mapping_to_run(item, source=f"cache:{source}")
                    if parsed_run:
                        runs.append(parsed_run)

                # 兼容一些仅存 last_results 的缓存结构
                last_results = raw.get("last_results")
                if isinstance(last_results, dict):
                    for key, result in last_results.items():
                        parsed_task = _mapping_to_task(
                            {
                                "id": key,
                                "name": key,
                                "schedule": "unknown",
                                "enabled": True,
                                "last_result": result,
                            },
                            source=f"cache:{source}",
                        )
                        if parsed_task:
                            tasks.append(parsed_task)

            elif isinstance(raw, list):
                for item in raw:
                    parsed_run = _mapping_to_run(item, source=f"cache:{source}")
                    if parsed_run:
                        runs.append(parsed_run)

        except json.JSONDecodeError as e:
            errors.append(f"缓存文件解析失败（{source}）：{e}")
        except OSError as e:
            errors.append(f"读取缓存文件失败（{source}）：{e}")

    if not tasks and not runs:
        warnings.append("未发现定时任务缓存文件，已使用日志推断执行记录")

    return tasks, runs


def _load_runs_from_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                items.append(obj)
    return items


def _build_tasks_and_runs_from_logs(*, warnings: List[str]) -> Tuple[List[SchedulerTaskItem], List[SchedulerRunItem]]:
    specs = [
        {
            "id": "health_check",
            "name": "服务健康检查",
            "file": PROJECT_ROOT / "logs" / "health_check.log",
            "start_markers": ["服务健康检查开始"],
            "fallback_schedule": "*/5 * * * * (inferred)",
        },
        {
            "id": "service_restart",
            "name": "服务监控与自动重启",
            "file": PROJECT_ROOT / "logs" / "service_restart.log",
            "start_markers": ["服务监控和自动重启脚本启动"],
            "fallback_schedule": "*/1 * * * * (inferred)",
        },
        {
            "id": "service_monitor",
            "name": "服务日志管理",
            "file": PROJECT_ROOT / "logs" / "service_monitor.log",
            "start_markers": ["开始服务日志管理"],
            "fallback_schedule": "*/5 * * * * (inferred)",
        },
    ]

    tasks: List[SchedulerTaskItem] = []
    runs: List[SchedulerRunItem] = []

    for spec in specs:
        task_id = spec["id"]
        log_file: Path = spec["file"]
        source = f"logs:{log_file.relative_to(PROJECT_ROOT)}"

        if not log_file.exists():
            warnings.append(f"日志文件不存在：{log_file}")
            tasks.append(
                SchedulerTaskItem(
                    id=task_id,
                    name=spec["name"],
                    schedule=spec["fallback_schedule"],
                    enabled=False,
                    source=source,
                    last_status="no_data",
                    last_result="日志文件不存在",
                )
            )
            continue

        task_runs = _parse_runs_from_log(
            log_file,
            task_id=task_id,
            start_markers=spec["start_markers"],
            source=source,
        )
        runs.extend(task_runs)

        last_run = task_runs[0] if task_runs else None
        schedule, next_run = _infer_schedule_and_next_run(task_runs)
        if not schedule:
            schedule = spec["fallback_schedule"]

        tasks.append(
            SchedulerTaskItem(
                id=task_id,
                name=spec["name"],
                schedule=schedule,
                enabled=True,
                source=source,
                next_run=next_run,
                last_run=last_run.started_at if last_run else None,
                last_status=last_run.status if last_run else "no_data",
                last_result=last_run.result if last_run else "暂无执行记录",
            )
        )

    return tasks, runs


def _parse_runs_from_log(
    log_file: Path,
    *,
    task_id: str,
    start_markers: List[str],
    source: Optional[str] = None,
) -> List[SchedulerRunItem]:
    lines = _tail_lines(log_file, max_bytes=900_000)
    entries: List[Tuple[datetime, str, str]] = []

    for line in lines:
        matched = LOG_LINE_RE.match(line)
        if not matched:
            continue
        ts = _parse_datetime(matched.group("ts"))
        if ts is None:
            continue
        level = matched.group("level").upper()
        message = matched.group("msg").strip()
        entries.append((ts, level, message))

    if not entries:
        return []

    start_indices: List[int] = []
    for i, (_, _, message) in enumerate(entries):
        if any(marker in message for marker in start_markers):
            start_indices.append(i)

    if not start_indices:
        start_indices = [0]

    runs: List[SchedulerRunItem] = []
    for i, start_idx in enumerate(start_indices):
        end_idx = start_indices[i + 1] - 1 if i + 1 < len(start_indices) else len(entries) - 1
        chunk = entries[start_idx : end_idx + 1]
        if not chunk:
            continue

        started_at = chunk[0][0]
        ended_at = chunk[-1][0]
        status = _chunk_status(chunk)
        result = _chunk_result(chunk)
        duration_ms = max(int((ended_at - started_at).total_seconds() * 1000), 0)

        runs.append(
            SchedulerRunItem(
                task_id=task_id,
                started_at=started_at,
                ended_at=ended_at,
                duration_ms=duration_ms,
                status=status,
                result=result,
                source=source,
            )
        )

    runs.sort(key=lambda x: x.started_at, reverse=True)
    return runs[:40]


def _tail_lines(file_path: Path, *, max_bytes: int) -> List[str]:
    with file_path.open("rb") as f:
        f.seek(0, 2)
        size = f.tell()
        start = max(0, size - max_bytes)
        f.seek(start)
        raw = f.read()

    text = raw.decode("utf-8", errors="ignore")
    lines = text.splitlines()
    if start > 0 and lines:
        # 可能截断了第一行，直接丢弃
        lines = lines[1:]
    return lines


def _chunk_status(chunk: List[Tuple[datetime, str, str]]) -> str:
    levels = {level for _, level, _ in chunk}
    messages = [msg for _, _, msg in chunk]

    if "ERROR" in levels or any("失败" in msg for msg in messages):
        return "failed"
    if "WARN" in levels or any("异常" in msg for msg in messages):
        return "warning"
    if "OK" in levels or any("正常" in msg or "完成" in msg for msg in messages):
        return "success"
    return "unknown"


def _chunk_result(chunk: List[Tuple[datetime, str, str]]) -> Optional[str]:
    for _, _, msg in reversed(chunk):
        msg = msg.strip()
        if not msg:
            continue
        if set(msg) == {"="}:
            continue
        return msg[:300]
    return None


def _infer_schedule_and_next_run(runs: List[SchedulerRunItem]) -> Tuple[Optional[str], Optional[datetime]]:
    if len(runs) < 2:
        return None, None

    ordered = sorted(runs, key=lambda x: x.started_at)
    deltas: List[int] = []
    for prev, curr in zip(ordered, ordered[1:]):
        diff = int((curr.started_at - prev.started_at).total_seconds())
        if diff > 0:
            deltas.append(diff)

    if not deltas:
        return None, None

    inferred = int(median(deltas))
    schedule = _interval_to_schedule(inferred)

    next_run = None
    latest = runs[0].started_at
    if inferred > 0:
        next_run = latest + timedelta(seconds=inferred)

    return schedule, next_run


def _interval_to_schedule(seconds: int) -> str:
    if seconds <= 0:
        return "unknown"

    if seconds % 60 == 0:
        minutes = seconds // 60
        if minutes == 1:
            return "*/1 * * * * (inferred)"
        if 1 < minutes < 60:
            return f"*/{minutes} * * * * (inferred)"

    if seconds % 3600 == 0:
        hours = seconds // 3600
        if hours == 1:
            return "0 * * * * (inferred)"
        return f"0 */{hours} * * * (inferred)"

    return f"every {seconds}s (inferred)"


def _mapping_to_task(raw: Any, *, source: str) -> Optional[SchedulerTaskItem]:
    if not isinstance(raw, dict):
        return None

    task_id = _as_str(_pick_first(raw, ("id", "task_id", "name", "key")))
    if not task_id:
        return None

    name = _as_str(_pick_first(raw, ("name", "title", "description"))) or task_id
    schedule = _normalize_schedule(_pick_first(raw, SCHEDULE_FIELDS)) or "unknown"

    enabled_raw = _pick_first(raw, ("enabled", "active", "is_enabled"))
    enabled = True if enabled_raw is None else bool(enabled_raw)

    return SchedulerTaskItem(
        id=task_id,
        name=name,
        schedule=schedule,
        enabled=enabled,
        source=source,
        next_run=_parse_datetime(_pick_first(raw, ("next_run", "next_at", "nextRun"))),
        last_run=_parse_datetime(_pick_first(raw, ("last_run", "last_at", "lastRun"))),
        last_status=_as_str(_pick_first(raw, RUN_STATUS_KEYS)),
        last_result=_as_str(_pick_first(raw, RUN_RESULT_KEYS)),
    )


def _mapping_to_run(raw: Any, *, source: Optional[str] = None) -> Optional[SchedulerRunItem]:
    if not isinstance(raw, dict):
        return None

    task_id = _as_str(_pick_first(raw, ("task_id", "taskId", "id", "name")))
    if not task_id:
        return None

    started_at = _parse_datetime(_pick_first(raw, RUN_START_KEYS))
    if started_at is None:
        return None

    ended_at = _parse_datetime(_pick_first(raw, RUN_END_KEYS))

    duration_raw = _pick_first(raw, ("duration_ms", "duration", "elapsed_ms"))
    duration_ms = None
    if isinstance(duration_raw, (int, float)):
        duration_ms = int(duration_raw)
    elif isinstance(duration_raw, str) and duration_raw.isdigit():
        duration_ms = int(duration_raw)
    elif ended_at is not None:
        duration_ms = max(int((ended_at - started_at).total_seconds() * 1000), 0)

    status = _as_str(_pick_first(raw, RUN_STATUS_KEYS)) or "unknown"
    result = _as_str(_pick_first(raw, RUN_RESULT_KEYS))

    run_source = source or _as_str(_pick_first(raw, ("source", "data_source")))

    return SchedulerRunItem(
        task_id=task_id,
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=duration_ms,
        status=status,
        result=result,
        source=run_source,
    )


def _attach_run_summary(tasks_map: Dict[str, SchedulerTaskItem], runs: List[SchedulerRunItem]) -> None:
    latest_by_task: Dict[str, SchedulerRunItem] = {}
    for run in sorted(runs, key=lambda x: x.started_at, reverse=True):
        if run.task_id not in latest_by_task:
            latest_by_task[run.task_id] = run

    for task_id, run in latest_by_task.items():
        task = tasks_map.get(task_id)
        if task is None:
            task = SchedulerTaskItem(
                id=task_id,
                name=task_id,
                schedule="unknown",
                enabled=True,
                source="derived:runs",
            )
            tasks_map[task_id] = task

        task.last_run = run.started_at
        task.last_status = run.status
        task.last_result = run.result


def _merge_task(tasks_map: Dict[str, SchedulerTaskItem], incoming: SchedulerTaskItem) -> None:
    existing = tasks_map.get(incoming.id)
    if existing is None:
        tasks_map[incoming.id] = incoming
        return

    if _source_priority(incoming.source) > _source_priority(existing.source):
        preferred, fallback = incoming, existing
    else:
        preferred, fallback = existing, incoming

    tasks_map[incoming.id] = SchedulerTaskItem(
        id=preferred.id,
        name=preferred.name or fallback.name,
        schedule=(preferred.schedule if preferred.schedule != "unknown" else fallback.schedule),
        enabled=preferred.enabled if preferred.enabled is not None else fallback.enabled,
        source=preferred.source,
        next_run=preferred.next_run or fallback.next_run,
        last_run=preferred.last_run or fallback.last_run,
        last_status=preferred.last_status or fallback.last_status,
        last_result=preferred.last_result or fallback.last_result,
    )


def _source_priority(source: str) -> int:
    if source.startswith("openclaw_config"):
        return 30
    if source.startswith("cache"):
        return 20
    if source.startswith("logs"):
        return 10
    return 0


def _pick_first(data: Dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in data:
            value = data.get(key)
            if value is not None:
                return value
    return None


def _normalize_schedule(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    if isinstance(value, (int, float)):
        return f"every {int(value)}s"
    if isinstance(value, dict):
        if "cron" in value:
            return _normalize_schedule(value.get("cron"))
        if "interval" in value:
            interval = value.get("interval")
            return _normalize_schedule(interval)
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        return _normalize_datetime(value)

    if isinstance(value, (int, float)):
        # 支持秒/毫秒时间戳
        ts = float(value)
        if ts > 10_000_000_000:
            ts = ts / 1000.0
        try:
            return _normalize_datetime(datetime.fromtimestamp(ts))
        except (ValueError, OSError):
            return None

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None

        if text.isdigit():
            return _parse_datetime(int(text))

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                return _normalize_datetime(datetime.strptime(text, fmt))
            except ValueError:
                pass

        # 兼容 ISO 格式（可能带时区）
        try:
            return _normalize_datetime(datetime.fromisoformat(text.replace("Z", "+00:00")))
        except ValueError:
            return None

    return None


def _normalize_datetime(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _as_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return str(value)
