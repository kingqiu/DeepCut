"""FFmpeg 批量视频切割：根据切片计划生成 MP4 文件"""

from pathlib import Path

from loguru import logger

from deepcut.exceptions import FFmpegError
from deepcut.models.clip import ClipPlan
from deepcut.video.extract import extract_clip


def batch_cut(
    video_path: Path,
    clip_plans: list[ClipPlan],
    output_dir: Path,
    codec: str = "copy",
) -> list[Path]:
    """批量切割视频，返回输出文件路径列表

    Args:
        video_path: 源视频路径
        clip_plans: 切片计划列表
        output_dir: 输出目录（clips/ 子目录）
        codec: 编码方式，'copy' 为无损快速提取

    Returns:
        输出文件路径列表

    Raises:
        FFmpegError: 任何切片失败时
    """
    clips_dir = output_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    output_paths: list[Path] = []
    total = len(clip_plans)

    logger.info(f"开始批量切割: {total} 个切片, codec={codec}")

    for plan in clip_plans:
        file_name = format_clip_filename(plan.index, total)
        output_path = clips_dir / file_name

        try:
            extract_clip(
                video_path=video_path,
                output_path=output_path,
                start=plan.start,
                end=plan.end,
                codec=codec,
            )
            output_paths.append(output_path)
            logger.debug(
                f"切片 {plan.index + 1}/{total}: "
                f"{plan.start:.1f}-{plan.end:.1f}s → {file_name}"
            )
        except FFmpegError as e:
            logger.error(f"切片 {plan.index} 失败: {e}")
            raise

    logger.info(f"批量切割完成: {len(output_paths)}/{total} 个切片")
    return output_paths


def format_clip_filename(index: int, total: int) -> str:
    """生成切片文件名

    根据总数自动决定零填充宽度：
    - < 100 片段: clip_00.mp4
    - < 1000 片段: clip_000.mp4
    - >= 1000 片段: clip_0000.mp4
    """
    if total >= 1000:
        width = 4
    elif total >= 100:
        width = 3
    else:
        width = 3  # 默认 3 位宽度
    return f"clip_{str(index).zfill(width)}.mp4"
