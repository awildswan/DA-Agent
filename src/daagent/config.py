"""配置：pydantic-settings 统一读 .env（对齐 comet 配置管理）。"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 模型（DeepSeek，OpenAI 兼容）
    openai_api_key: str = ""
    openai_api_base: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"

    # 查询
    query_row_limit: int = 200


def get_settings() -> Settings:
    return Settings()
