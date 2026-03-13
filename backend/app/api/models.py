"""
模型管理 API - 从 OpenClaw 配置文件获取可用模型列表
"""
from __future__ import annotations

import json
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.settings import get_settings

router = APIRouter()
settings = get_settings()


class ModelInfo(BaseModel):
    id: str
    full_id: str
    name: str
    provider: str
    contextWindow: int
    maxTokens: int
    input: List[str]
    reasoning: bool = False


class ProviderInfo(BaseModel):
    name: str
    baseUrl: str
    models: List[ModelInfo]


class ModelsResponse(BaseModel):
    providers: List[ProviderInfo]


@router.get("/available", response_model=ModelsResponse)
async def get_available_models():
    path = settings.openclaw_config_path
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"OpenClaw 配置文件不存在：{path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"配置文件解析失败：{e}") from e

    providers: List[ProviderInfo] = []
    for provider_name, provider_data in config.get("models", {}).get("providers", {}).items():
        model_items: List[ModelInfo] = []
        for model in provider_data.get("models", []):
            model_id = (model.get("id") or "").strip()
            if not model_id:
                continue
            model_items.append(
                ModelInfo(
                    id=model_id,
                    full_id=f"{provider_name}/{model_id}",
                    name=model.get("name") or model_id,
                    provider=provider_name,
                    contextWindow=int(model.get("contextWindow") or 0),
                    maxTokens=int(model.get("maxTokens") or 0),
                    input=model.get("input") or [],
                    reasoning=bool(model.get("reasoning") or False),
                )
            )

        if model_items:
            providers.append(
                ProviderInfo(
                    name=provider_name,
                    baseUrl=provider_data.get("baseUrl") or "",
                    models=model_items,
                )
            )

    return ModelsResponse(providers=providers)


@router.get("/schema")
async def get_model_schema():
    return {
        "models.providers[].models[]": {
            "required_fields": ["id", "name", "reasoning", "input", "cost", "contextWindow", "maxTokens"],
            "field_types": {
                "id": "string",
                "name": "string",
                "reasoning": "boolean",
                "input": "array",
                "cost": "object",
                "contextWindow": "number",
                "maxTokens": "number",
            },
        },
        "agents.list[].model": {
            "required_fields": ["primary"],
            "field_types": {
                "primary": "string (provider/model-id)",
            },
        },
    }
