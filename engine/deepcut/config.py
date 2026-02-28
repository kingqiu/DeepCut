"""全局配置：Pydantic Settings，读取环境变量 + .env 文件"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepCutConfig(BaseSettings):
    """DeepCut 切片引擎全局配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
    )

    # --- AI 服务 ---
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    openai_vision_model: str = "qwen3-vl-plus"
    dashscope_api_key: str = ""

    # --- Whisper ---
    whisper_model: Literal["tiny", "base", "small", "medium", "large-v3"] = "base"
    whisper_device: Literal["cpu", "cuda"] = "cpu"
    whisper_compute_type: Literal["float16", "int8"] = "int8"

    # --- 存储 ---
    deepcut_storage_root: Path = Path.home() / "deepcut-data"

    # --- 切片引擎 ---
    deepcut_default_min_duration: float = 15.0
    deepcut_default_max_duration: float = 60.0
    deepcut_overlap_duration: float = 1.5
    deepcut_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


def get_config(env_file: Path | None = None) -> DeepCutConfig:
    """获取配置实例，可指定 .env 文件路径"""
    if env_file is not None:
        return DeepCutConfig(_env_file=env_file)  # type: ignore[call-arg]
    return DeepCutConfig()
