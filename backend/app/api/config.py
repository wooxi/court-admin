"""
OpenClaw 配置管理 API
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.settings import get_settings

router = APIRouter()
settings = get_settings()


class ConfigUpdate(BaseModel):
    config_key: str = "openclaw"
    config_value: dict


class RestoreRequest(BaseModel):
    filename: str = Field(min_length=1)


class ReloadRequest(BaseModel):
    perform: bool = True
    timeout_seconds: int = Field(default=20, ge=3, le=120)


def require_admin_token(x_admin_token: Optional[str] = Header(default=None)):
    """
    若设置了 CONFIG_ADMIN_TOKEN，则要求请求头 X-Admin-Token 匹配。
    """
    expected = settings.config_admin_token
    if expected and x_admin_token != expected:
        raise HTTPException(status_code=401, detail="管理员令牌无效")


def _load_config() -> Dict[str, Any]:
    path = settings.openclaw_config_path
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"配置文件不存在：{path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"配置文件解析失败：{e}") from e


def _save_config(config: Dict[str, Any]) -> None:
    path = settings.openclaw_config_path
    with path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def _create_backup() -> str:
    backup_dir = settings.backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"openclaw-backup-{timestamp}.json"
    backup_path = backup_dir / filename

    shutil.copy2(settings.openclaw_config_path, backup_path)
    return str(backup_path)


def _normalize_model_primary(raw_primary: str, config: Dict[str, Any]) -> str:
    """
    支持前端传裸 model id（如 qwen3.5-plus）或完整 provider/model（如 bailian/qwen3.5-plus）。
    """
    value = (raw_primary or "").strip()
    if not value:
        raise HTTPException(status_code=400, detail="model.primary 不能为空")

    if "/" in value:
        return value

    providers = config.get("models", {}).get("providers", {})
    for provider_name, provider_data in providers.items():
        for model in provider_data.get("models", []):
            if model.get("id") == value:
                return f"{provider_name}/{value}"

    raise HTTPException(status_code=400, detail=f"未找到模型：{value}，请使用 provider/model 格式")


@router.get("/")
async def get_config(_=Depends(require_admin_token)):
    config = _load_config()
    return {
        "config_key": "openclaw",
        "config_value": config,
        "version": config.get("meta", {}).get("lastTouchedVersion", "unknown"),
        "updated_at": config.get("meta", {}).get("lastTouchedAt", "unknown"),
    }


@router.get("/ministers")
async def get_ministers_config(_=Depends(require_admin_token)):
    config = _load_config()
    agents = config.get("agents", {}).get("list", [])

    return {
        "ministers": [
            {
                "id": agent.get("id"),
                "name": agent.get("name"),
                "workspace": agent.get("workspace"),
                "model": agent.get("model") or {},
                "identity": agent.get("identity") or {},
                "sandbox": agent.get("sandbox") or {},
                "subagents": agent.get("subagents") or {},
            }
            for agent in agents
        ]
    }


@router.put("/ministers/{minister_id}")
async def update_minister_config(
    minister_id: str,
    config_update: ConfigUpdate,
    _=Depends(require_admin_token),
):
    config = _load_config()

    agents = config.get("agents", {}).get("list", [])
    target_agent = None
    for agent in agents:
        if agent.get("id") == minister_id:
            target_agent = agent
            break

    if target_agent is None:
        raise HTTPException(status_code=404, detail=f"大臣不存在：{minister_id}")

    update_data = config_update.config_value
    allowed_fields = {"model", "workspace", "identity", "sandbox", "subagents"}

    unknown = set(update_data.keys()) - allowed_fields
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"不允许修改的字段：{sorted(unknown)}，允许字段：{sorted(allowed_fields)}",
        )

    # 先备份
    backup_path = _create_backup()

    # 更新逻辑
    for key, value in update_data.items():
        if key == "model":
            if not isinstance(value, dict):
                raise HTTPException(status_code=400, detail="model 必须是对象")

            model_obj = dict(target_agent.get("model") or {})
            model_obj.update(value)
            if "primary" in model_obj:
                model_obj["primary"] = _normalize_model_primary(model_obj["primary"], config)
            target_agent["model"] = model_obj
        else:
            target_agent[key] = value

    _save_config(config)

    return {
        "message": "配置更新成功",
        "backup_path": backup_path,
        "minister_id": minister_id,
    }


@router.post("/backup")
async def create_config_backup(_=Depends(require_admin_token)):
    backup_path = _create_backup()
    return {"message": "备份成功", "backup_path": backup_path}


@router.get("/backups")
async def list_backups(_=Depends(require_admin_token)):
    backup_dir = settings.backup_dir
    if not backup_dir.exists():
        return {"backups": []}

    backups = []
    for file in backup_dir.glob("openclaw-backup-*.json"):
        stat = file.stat()
        backups.append(
            {
                "filename": file.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )

    backups.sort(key=lambda x: x["created_at"], reverse=True)
    return {"backups": backups}


@router.post("/restore")
async def restore_backup(payload: RestoreRequest, _=Depends(require_admin_token)):
    backup_file = settings.backup_dir / payload.filename
    if not backup_file.exists():
        raise HTTPException(status_code=404, detail="备份文件不存在")

    # 先备份当前配置，再恢复
    current_backup = _create_backup()
    shutil.copy2(backup_file, settings.openclaw_config_path)

    return {
        "message": "恢复成功",
        "restored_from": str(backup_file),
        "current_backup": current_backup,
    }


@router.delete("/backups/{filename}")
async def delete_backup(filename: str, _=Depends(require_admin_token)):
    backup_file = settings.backup_dir / filename
    if not backup_file.exists():
        raise HTTPException(status_code=404, detail="备份文件不存在")

    backup_file.unlink()
    return {"message": "删除成功", "filename": filename}


@router.post("/reload")
async def reload_config(payload: ReloadRequest = ReloadRequest(), _=Depends(require_admin_token)):
    """
    触发 OpenClaw 网关重启以应用配置。
    """
    if not payload.perform:
        return {
            "message": "已跳过执行",
            "note": "传 perform=true 可执行实际重载",
        }

    if not settings.enable_reload_command:
        raise HTTPException(status_code=403, detail="当前环境禁用了 reload 命令执行")

    try:
        result = subprocess.run(
            settings.openclaw_reload_command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=payload.timeout_seconds,
        )
    except subprocess.TimeoutExpired as e:
        raise HTTPException(status_code=504, detail=f"重载超时：{e}") from e

    return {
        "message": "重载命令执行完成",
        "command": settings.openclaw_reload_command,
        "return_code": result.returncode,
        "stdout": (result.stdout or "")[:2000],
        "stderr": (result.stderr or "")[:2000],
    }
