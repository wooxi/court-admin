"""
大臣管理 API
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.models import get_db
from app.models.minister import Minister
from app.settings import get_settings

router = APIRouter()


class MinisterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    department: str = Field(min_length=1, max_length=50)
    model_id: str = Field(min_length=1, max_length=100)
    workspace: str = Field(min_length=1, max_length=500)
    api_key: Optional[str] = None
    enabled: bool = True


class MinisterUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    department: Optional[str] = Field(default=None, min_length=1, max_length=50)
    model_id: Optional[str] = Field(default=None, min_length=1, max_length=100)
    workspace: Optional[str] = Field(default=None, min_length=1, max_length=500)
    api_key: Optional[str] = None
    enabled: Optional[bool] = None


class MinisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    department: str
    model_id: str
    workspace: str
    enabled: bool


@router.get("/", response_model=List[MinisterResponse])
async def get_ministers(
    enabled: Optional[bool] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Minister)
    if enabled is not None:
        query = query.filter(Minister.enabled == enabled)
    return query.order_by(Minister.id.asc()).limit(limit).all()


@router.get("/{minister_id}", response_model=MinisterResponse)
async def get_minister(minister_id: int, db: Session = Depends(get_db)):
    minister = db.query(Minister).filter(Minister.id == minister_id).first()
    if not minister:
        raise HTTPException(status_code=404, detail="大臣不存在")
    return minister


@router.post("/", response_model=MinisterResponse, status_code=201)
async def create_minister(minister: MinisterCreate, db: Session = Depends(get_db)):
    exists = (
        db.query(Minister)
        .filter(Minister.name == minister.name, Minister.department == minister.department)
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="同名大臣已存在")

    db_minister = Minister(**minister.model_dump())
    db.add(db_minister)
    db.commit()
    db.refresh(db_minister)
    return db_minister


@router.put("/{minister_id}", response_model=MinisterResponse)
async def update_minister(minister_id: int, minister: MinisterUpdate, db: Session = Depends(get_db)):
    db_minister = db.query(Minister).filter(Minister.id == minister_id).first()
    if not db_minister:
        raise HTTPException(status_code=404, detail="大臣不存在")

    update_data = minister.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_minister, key, value)

    db.commit()
    db.refresh(db_minister)
    return db_minister


@router.delete("/{minister_id}")
async def delete_minister(minister_id: int, db: Session = Depends(get_db)):
    db_minister = db.query(Minister).filter(Minister.id == minister_id).first()
    if not db_minister:
        raise HTTPException(status_code=404, detail="大臣不存在")

    db.delete(db_minister)
    db.commit()
    return {"message": "删除成功"}


# 大臣 ID 映射 (database_id -> agent_id)
MINISTER_AGENT_MAP = {
    1: "silijian",
    2: "bingbu",
    3: "hubu",
    4: "libu",
    5: "gongbu",
    6: "libu2",
    7: "xingbu",
}

# 反向映射 (agent_id -> database_id)
AGENT_MINISTER_MAP = {v: k for k, v in MINISTER_AGENT_MAP.items()}


@router.get("/openclaw/config")
async def get_ministers_from_openclaw():
    """
    从 OpenClaw 配置文件读取最新大臣配置
    """
    settings = get_settings()
    config_path = Path(settings.openclaw_config_path)
    
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="OpenClaw 配置文件不存在")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        agents = config.get("agents", {}).get("list", [])
        result = []
        
        for agent in agents:
            agent_id = agent.get("id")
            db_id = AGENT_MINISTER_MAP.get(agent_id)
            if db_id:
                result.append({
                    "id": db_id,
                    "agent_id": agent_id,
                    "name": agent.get("name", ""),
                    "model_primary": agent.get("model", {}).get("primary", ""),
                    "workspace": agent.get("workspace", ""),
                    "enabled": agent.get("sandbox", {}).get("mode", "off") != "off",
                })
        
        return {"ok": True, "ministers": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取配置失败：{str(e)}")


@router.put("/openclaw/sync")
async def sync_ministers_to_openclaw(ministers: List[dict]):
    """
    将大臣配置同步到 OpenClaw 配置文件
    
    请求体：
    [
        {"id": 1, "model_primary": "bailian/qwen3.5-plus"},
        {"id": 2, "model_primary": "bailian/qwen3-coder-plus"},
        ...
    ]
    """
    settings = get_settings()
    config_path = Path(settings.openclaw_config_path)
    
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="OpenClaw 配置文件不存在")
    
    try:
        # 读取配置
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 构建映射
        update_map = {m["id"]: m.get("model_primary") for m in ministers if m.get("model_primary")}
        
        # 更新 agents.list
        agents = config.get("agents", {}).get("list", [])
        updated_count = 0
        
        for agent in agents:
            agent_id = agent.get("id")
            db_id = MINISTER_AGENT_MAP.get(agent_id)
            
            if db_id and db_id in update_map:
                new_model = update_map[db_id]
                old_model = agent.get("model", {}).get("primary", "")
                
                if old_model != new_model:
                    if "model" not in agent:
                        agent["model"] = {}
                    agent["model"]["primary"] = new_model
                    updated_count += 1
        
        # 写回配置
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 更新数据库
        db = next(get_db())
        for minister_data in ministers:
            if minister_data.get("model_primary"):
                db_minister = db.query(Minister).filter(Minister.id == minister_data["id"]).first()
                if db_minister:
                    db_minister.model_id = minister_data["model_primary"]
        
        db.commit()
        
        return {
            "ok": True,
            "message": f"已同步 {updated_count} 个大臣配置",
            "updated_count": updated_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步配置失败：{str(e)}")


@router.post("/openclaw/reload")
async def reload_openclaw_config():
    """
    从 OpenClaw 配置文件重新加载大臣配置到数据库
    """
    settings = get_settings()
    config_path = Path(settings.openclaw_config_path)
    
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="OpenClaw 配置文件不存在")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        agents = config.get("agents", {}).get("list", [])
        db = next(get_db())
        updated_count = 0
        updated_ministers = []
        
        for agent in agents:
            agent_id = agent.get("id")
            db_id = MINISTER_AGENT_MAP.get(agent_id)
            
            if db_id:
                db_minister = db.query(Minister).filter(Minister.id == db_id).first()
                if db_minister:
                    new_model = agent.get("model", {}).get("primary", "")
                    # 强制更新，不管是否相同
                    if db_minister.model_id != new_model:
                        db_minister.model_id = new_model
                        updated_count += 1
                        updated_ministers.append(f"{agent_id}({db_id}): {new_model}")
        
        if updated_count > 0:
            db.commit()
        
        return {
            "ok": True,
            "message": f"已从配置文件加载 {updated_count} 个更新",
            "updated_count": updated_count,
            "updated_ministers": updated_ministers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载配置失败：{str(e)}")
