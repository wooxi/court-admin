"""
模型管理 API - 从 OpenClaw 配置文件获取可用模型列表
"""
from fastapi import APIRouter, HTTPException
import json
import os
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# OpenClaw 配置文件路径
OPENCLAW_CONFIG_PATH = os.getenv(
    "OPENCLAW_CONFIG_PATH",
    "/root/.openclaw/openclaw.json"
)

class ModelInfo(BaseModel):
    id: str
    name: str
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
    """
    从 OpenClaw 配置文件获取可用模型列表
    
    流程：
    1. 读取 /root/.openclaw/openclaw.json
    2. 解析 models.providers[].models[] 数组
    3. 返回可用模型列表
    """
    try:
        # 检查配置文件是否存在
        if not os.path.exists(OPENCLAW_CONFIG_PATH):
            raise HTTPException(
                status_code=404,
                detail=f"OpenClaw 配置文件不存在：{OPENCLAW_CONFIG_PATH}"
            )
        
        # 读取配置文件
        with open(OPENCLAW_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 解析模型列表
        providers = []
        models_config = config.get("models", {})
        mode = models_config.get("mode", "merge")
        
        for provider_name, provider_data in models_config.get("providers", {}).items():
            models = []
            for model in provider_data.get("models", []):
                models.append(ModelInfo(
                    id=model.get("id", ""),
                    name=model.get("name", ""),
                    contextWindow=model.get("contextWindow", 0),
                    maxTokens=model.get("maxTokens", 0),
                    input=model.get("input", []),
                    reasoning=model.get("reasoning", False)
                ))
            
            if models:
                providers.append(ProviderInfo(
                    name=provider_name,
                    baseUrl=provider_data.get("baseUrl", ""),
                    models=models
                ))
        
        return ModelsResponse(providers=providers)
    
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"配置文件解析失败：{str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取模型列表失败：{str(e)}"
        )

@router.get("/schema")
async def get_model_schema():
    """
    获取 OpenClaw 模型配置 Schema
    
    用于前端验证字段规范性
    """
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
                "maxTokens": "number"
            }
        },
        "agents.list[].model": {
            "required_fields": ["primary"],
            "field_types": {
                "primary": "string"  # 格式：provider/model-id
            }
        }
    }
