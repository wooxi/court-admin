"""
应用配置
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # 始终从项目根目录读取 .env，避免在 backend 工作目录启动时读不到配置
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="mysql+pymysql://court_admin:court_admin_2026@localhost:3306/court_admin?charset=utf8mb4",
        alias="DATABASE_URL",
    )

    openclaw_config_path: Path = Field(
        default=Path("/root/.openclaw/openclaw.json"),
        alias="OPENCLAW_CONFIG_PATH",
    )

    backup_dir: Path = Field(
        default=Path("/root/court-admin/data/backups"),
        alias="BACKUP_DIR",
    )

    cors_origins: str = Field(
        default="http://localhost:9002,http://127.0.0.1:9002",
        alias="CORS_ORIGINS",
    )

    # 若设置该值，配置管理接口要求 X-Admin-Token 头部
    config_admin_token: Optional[str] = Field(default=None, alias="CONFIG_ADMIN_TOKEN")

    # 是否允许在接口内执行 openclaw reload 命令
    enable_reload_command: bool = Field(default=True, alias="ENABLE_RELOAD_COMMAND")

    openclaw_reload_command: str = Field(
        default="openclaw gateway restart",
        alias="OPENCLAW_RELOAD_COMMAND",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        raw = self.cors_origins.strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
