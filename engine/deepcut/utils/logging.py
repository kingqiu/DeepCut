"""日志配置：loguru，终端进度输出"""

import sys
from typing import Literal

from loguru import logger


def setup_logging(level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO") -> None:
    """配置 loguru 日志"""
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )


def step_log(step: int, total: int, name: str, message: str) -> None:
    """Pipeline 步骤日志"""
    logger.info(f"[Step {step}/{total}] {name} - {message}")


def step_start(step: int, total: int, name: str) -> None:
    """Pipeline 步骤开始"""
    logger.info(f"[Step {step}/{total}] {name} - 开始")


def step_done(step: int, total: int, name: str, elapsed: float) -> None:
    """Pipeline 步骤完成"""
    logger.success(f"[Step {step}/{total}] {name} - 完成 ({elapsed:.1f}s)")
