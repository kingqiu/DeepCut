"""FFmpeg 视频探测：提取视频基本信息"""

import json
import subprocess
from pathlib import Path

from loguru import logger

from deepcut.exceptions import FFmpegError
from deepcut.models.video import VideoInfo


def probe_video(video_path: Path) -> VideoInfo:
    """使用 ffprobe 探测视频信息

    Args:
        video_path: 视频文件路径

    Returns:
        VideoInfo 数据模型

    Raises:
        FFmpegError: ffprobe 调用失败
    """
    if not video_path.exists():
        raise FFmpegError(f"视频文件不存在: {video_path}")

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as e:
        raise FFmpegError(f"ffprobe 超时: {video_path}") from e
    except FileNotFoundError as e:
        raise FFmpegError("ffprobe 未安装，请安装 FFmpeg") from e

    if result.returncode != 0:
        raise FFmpegError(f"ffprobe 失败 (exit {result.returncode}): {result.stderr}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise FFmpegError(f"ffprobe 输出解析失败: {e}") from e

    video_stream = _find_stream(data, "video")
    audio_stream = _find_stream(data, "audio")
    fmt = data.get("format", {})

    if video_stream is None:
        raise FFmpegError(f"未找到视频流: {video_path}")

    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    duration = float(fmt.get("duration", video_stream.get("duration", 0)))
    file_size = int(fmt.get("size", 0))

    fps_str = video_stream.get("r_frame_rate", "30/1")
    fps = _parse_fps(fps_str)

    codec = video_stream.get("codec_name", "unknown")
    audio_codec = audio_stream.get("codec_name", "") if audio_stream else ""
    has_audio = audio_stream is not None

    orientation = _determine_orientation(width, height)

    info = VideoInfo(
        path=video_path,
        duration=duration,
        width=width,
        height=height,
        fps=fps,
        codec=codec,
        audio_codec=audio_codec,
        has_audio=has_audio,
        orientation=orientation,
        file_size=file_size,
    )

    logger.debug(
        f"视频信息: {width}x{height} {fps:.1f}fps {codec} "
        f"{duration:.1f}s {orientation} audio={has_audio}"
    )

    return info


def _find_stream(data: dict, codec_type: str) -> dict | None:  # type: ignore[type-arg]
    """从 ffprobe 输出中找到指定类型的流"""
    for stream in data.get("streams", []):
        if stream.get("codec_type") == codec_type:
            return stream  # type: ignore[no-any-return]
    return None


def _parse_fps(fps_str: str) -> float:
    """解析帧率字符串，如 '30/1' → 30.0"""
    try:
        if "/" in fps_str:
            num, den = fps_str.split("/")
            den_val = int(den)
            if den_val == 0:
                return 30.0
            return int(num) / den_val
        return float(fps_str)
    except (ValueError, ZeroDivisionError):
        return 30.0


def _determine_orientation(width: int, height: int) -> str:
    """根据宽高判断画幅方向"""
    if width == 0 or height == 0:
        return "landscape"
    ratio = width / height
    if ratio > 1.1:
        return "landscape"
    elif ratio < 0.9:
        return "portrait"
    else:
        return "square"
