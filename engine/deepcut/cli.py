"""CLI 入口：typer"""

from pathlib import Path
from typing import Annotated, Optional

import typer

from deepcut import __version__
from deepcut.config import get_config
from deepcut.utils.logging import setup_logging

app = typer.Typer(
    name="deepcut",
    help="DeepCut - 智能短视频切片引擎",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"DeepCut v{__version__}")
        raise typer.Exit()


@app.command()
def slice(
    input_path: Annotated[
        Path,
        typer.Argument(help="输入视频路径", exists=True, readable=True),
    ],
    output_dir: Annotated[
        Optional[Path],
        typer.Option("--output-dir", "-o", help="输出目录（默认：视频所在目录/deepcut_output/）"),
    ] = None,
    duration_min: Annotated[
        Optional[float],
        typer.Option("--duration-min", help="最小切片时长参考值（秒）"),
    ] = None,
    duration_max: Annotated[
        Optional[float],
        typer.Option("--duration-max", help="最大切片时长参考值（秒）"),
    ] = None,
    disable_motion: Annotated[
        bool,
        typer.Option("--no-motion", help="禁用运镜检测"),
    ] = False,
    disable_speech: Annotated[
        bool,
        typer.Option("--no-speech", help="禁用语音分析（强制走视觉优先路径）"),
    ] = False,
    env_file: Annotated[
        Optional[Path],
        typer.Option("--env-file", help=".env 文件路径"),
    ] = None,
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """对视频进行智能切片"""
    config = get_config(env_file=env_file)

    if duration_min is not None:
        config.deepcut_default_min_duration = duration_min
    if duration_max is not None:
        config.deepcut_default_max_duration = duration_max

    setup_logging(config.deepcut_log_level)

    from loguru import logger

    from deepcut.pipeline.orchestrator import PipelineOrchestrator

    logger.info(f"DeepCut v{__version__}")
    logger.info(f"输入视频: {input_path}")
    logger.info(f"切片时长参考: {config.deepcut_default_min_duration}~{config.deepcut_default_max_duration}s")
    logger.info(f"运镜检测: {'禁用' if disable_motion else '启用'}")
    logger.info(f"语音分析: {'禁用' if disable_speech else '启用'}")

    orchestrator = PipelineOrchestrator(
        config=config,
        disable_motion=disable_motion,
        disable_speech=disable_speech,
    )

    try:
        version_dir = orchestrator.run(
            input_path=input_path,
            output_dir=output_dir,
        )
        logger.success(f"切片完成! 输出: {version_dir}")
    except Exception as e:
        logger.error(f"切片失败: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
