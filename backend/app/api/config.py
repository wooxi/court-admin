"""
OpenClaw 配置管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import os
import shutil
from datetime import datetime
from typing import List, Optional
from app.models import get_db
from app.models.config_model import OpenClawConfig
from pydantic import BaseModel

router = APIRouter()

# OpenClaw 配置文件路径
OPENCLAW_CONFIG_PATH = os.getenv(
    "OPENCLAW_CONFIG_PATH",
    "/root/.openclaw/openclaw.json"
)

# 备份目录
BACKUP_DIR = os.getenv("BACKUP_DIR", "/root/court-admin/data/backups")

class ConfigResponse(BaseModel):
    config_key: str
    config_value: dict
    version: str
    updated_at: datetime

class ConfigUpdate(BaseModel):
    config_key: str
    config_value: dict

@router.get("/")
async def get_config(db: Session = Depends(get_db)):
    """
    获取 OpenClaw 配置
    
    直接从配置文件读取，确保数据最新
    """
    try:
        if not os.path.exists(OPENCLAW_CONFIG_PATH):
            raise HTTPException(
                status_code=404,
                detail=f"配置文件不存在：{OPENCLAW_CONFIG_PATH}"
            )
        
        with open(OPENCLAW_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return {
            "config_key": "openclaw",
            "config_value": config,
            "version": config.get("meta", {}).get("lastTouchedVersion", "unknown"),
            "updated_at": config.get("meta", {}).get("lastTouchedAt", "unknown")
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"配置文件解析失败：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取配置失败：{str(e)}")

@router.get("/ministers")
async def get_ministers_config(db: Session = Depends(get_db)):
    """
    获取大臣配置（从 openclaw.json 的 agents.list 提取）
    """
    try:
        with open(OPENCLAW_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        agents = config.get("agents", {}).get("list", [])
        
        return {
            "ministers": [
                {
                    "id": agent.get("id"),
                    "name": agent.get("name"),
                    "workspace": agent.get("workspace"),
                    "model": agent.get("model"),
                    "identity": agent.get("identity"),
                    "sandbox": agent.get("sandbox"),
                    "subagents": agent.get("subagents")
                }
                for agent in agents
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取大臣配置失败：{str(e)}")

@router.put("/ministers/{minister_id}")
async def update_minister_config(
    minister_id: str,
    config_update: ConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    更新大臣配置
    
    ⚠️ 重要：
    1. 必须先验证字段规范性
    2. 更新前必须备份
    3. 更新后必须热重载
    """
    try:
        # 1. 读取当前配置
        with open(OPENCLAW_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 2. 查找大臣配置
        agents = config.get("agents", {}).get("list", [])
        minister_index = None
        for i, agent in enumerate(agents):
            if agent.get("id") == minister_id:
                minister_index = i
                break
        
        if minister_index is None:
            raise HTTPException(status_code=404, detail=f"大臣不存在：{minister_id}")
        
        # 3. 验证字段规范性
        update_data = config_update.config_value
        allowed_fields = ["model", "workspace", "identity", "sandbox", "subagents"]
        for key in update_data.keys():
            if key not in allowed_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"不允许修改的字段：{key}。允许字段：{allowed_fields}"
                )
        
        # 4. 备份当前配置
        backup_path = create_backup()
        
        # 5. 更新配置
        for key, value in update_data.items():
            agents[minister_index][key] = value
        
        # 6. 写回配置文件
        with open(OPENCLAW_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 7. 调用热重载（TODO: 实现 OpenClaw 热重载 API 调用）
        # await reload_openclaw()
        
        return {
            "message": "配置更新成功",
            "backup_path": backup_path,
            "minister_id": minister_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败：{str(e)}")

def create_backup() -> str:
    """创建配置备份"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_filename = f"openclaw-backup-{timestamp}.json"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    shutil.copy2(OPENCLAW_CONFIG_PATH, backup_path)
    return backup_path

@router.post("/backup")
async def create_config_backup():
    """手动创建配置备份"""
    try:
        backup_path = create_backup()
        return {
            "message": "备份成功",
            "backup_path": backup_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"备份失败：{str(e)}")

@router.get("/backups")
async def list_backups():
    """列出所有备份"""
    try:
        if not os.path.exists(BACKUP_DIR):
            return {"backups": []}
        
        backups = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith("openclaw-backup-"):
                filepath = os.path.join(BACKUP_DIR, filename)
                stat = os.stat(filepath)
                backups.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # 按时间倒序
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return {"backups": backups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出备份失败：{str(e)}")

@router.post("/reload")
async def reload_config():
    """
    热重载 OpenClaw 配置
    
    TODO: 调用 OpenClaw 热重载 API
    """
    return {
        "message": "热重载功能待实现",
        "note": "需要调用 OpenClaw 的重新加载配置接口"
    }
