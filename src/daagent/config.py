"""配置：pydantic-settings 统一读 .env（对齐 comet 配置管理）。"""

import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_file() -> str:
    """找 .env：优先 exe 同目录（绿色版用户自己放），其次冻结包目录，最后 CWD。"""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        if (exe_dir / ".env").exists():
            return str(exe_dir / ".env")
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and (Path(meipass) / ".env").exists():
            return str(Path(meipass) / ".env")
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file(), env_file_encoding="utf-8", extra="ignore"
    )

    # 模型（DeepSeek，OpenAI 兼容）
    openai_api_key: str = ""
    openai_api_base: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"

    # 查询
    query_row_limit: int = 200


def get_settings() -> Settings:
    return Settings()
