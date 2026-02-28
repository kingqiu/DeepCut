"""FFmpeg 视频/音频提取操作"""

import subprocess
from pathlib import Path

from loguru import logger

from deepcut.exceptions import FFmpegError


def extract_audio(
    video_path: Path,
    output_path: Path,
    sample_rate: int = 16000,
    normalize: bool = True,
) -> Path:
    """从视频中提取音频为 WAV 格式（供 VAD / Whisper 使用）

    Args:
        video_path: 输入视频路径
        output_path: 输出 WAV 文件路径
        sample_rate: 采样率（默认 16000Hz，Whisper 要求）
        normalize: 是否使用 loudnorm 标准化音量（提升 VAD 检测准确率）

    Returns:
        输出文件路径

    Raises:
        FFmpegError: FFmpeg 调用失败
    """
    af_filters = []
    if normalize:
        af_filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",                          # 不要视频
        "-acodec", "pcm_s16le",         # 16-bit PCM
        "-ar", str(sample_rate),        # 采样率
        "-ac", "1",                     # 单声道
    ]

    if af_filters:
        cmd.extend(["-af", ",".join(af_filters)])

    cmd.extend(["-y", str(output_path)])

    logger.debug(f"提取音频: {video_path} → {output_path}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired as e:
        raise FFmpegError(f"FFmpeg 音频提取超时: {video_path}") from e
    except FileNotFoundError as e:
        raise FFmpegError("FFmpeg 未安装") from e

    if result.returncode != 0:
        raise FFmpegError(f"FFmpeg 音频提取失败 (exit {result.returncode}): {result.stderr}")

    if not output_path.exists():
        raise FFmpegError(f"FFmpeg 音频提取后文件不存在: {output_path}")

    logger.debug(f"音频提取完成: {output_path} ({output_path.stat().st_size / 1024:.0f}KB)")
    return output_path


def extract_frame(
    video_path: Path,
    output_path: Path,
    timestamp: float,
    width: int = 512,
) -> Path:
    """从视频中截取指定时间点的帧为 JPEG 图片

    Args:
        video_path: 输入视频路径
        output_path: 输出 JPEG 文件路径
        timestamp: 截取时间点（秒）
        width: 输出图片宽度（等比缩放，默认 512px 节省 token）

    Returns:
        输出文件路径

    Raises:
        FFmpegError: FFmpeg 调用失败
    """
    cmd = [
        "ffmpeg",
        "-ss", f"{timestamp:.3f}",
        "-i", str(video_path),
        "-vframes", "1",
        "-vf", f"scale={width}:-2",
        "-q:v", "5",
        "-y",
        str(output_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as e:
        raise FFmpegError(f"FFmpeg 帧截取超时: {video_path} @ {timestamp}s") from e
    except FileNotFoundError as e:
        raise FFmpegError("FFmpeg 未安装") from e

    if result.returncode != 0:
        raise FFmpegError(
            f"FFmpeg 帧截取失败 @ {timestamp:.1f}s "
            f"(exit {result.returncode}): {result.stderr}"
        )

    if not output_path.exists():
        raise FFmpegError(f"FFmpeg 帧截取后文件不存在: {output_path}")

    return output_path


def extract_clip(
    video_path: Path,
    output_path: Path,
    start: float,
    end: float,
    codec: str = "copy",
) -> Path:
    """从视频中提取指定时间段的切片

    Args:
        video_path: 输入视频路径
        output_path: 输出切片路径
        start: 起始时间（秒）
        end: 结束时间（秒）
        codec: 编码方式，'copy' 为无损快速提取，'libx264' 为重编码

    Returns:
        输出文件路径

    Raises:
        FFmpegError: FFmpeg 调用失败
    """
    duration = end - start

    cmd = [
        "ffmpeg",
        "-ss", f"{start:.3f}",
        "-i", str(video_path),
        "-t", f"{duration:.3f}",
        "-c:v", codec,
    ]

    # H.264 重编码时添加质量和兼容性参数
    if codec == "libx264":
        cmd.extend([
            "-crf", "18",               # 高质量（视觉无损）
            "-preset", "fast",           # 编码速度
            "-pix_fmt", "yuv420p",       # 兼容 QuickTime / 浏览器
            "-movflags", "+faststart",   # Web 友好（moov atom 前置）
        ])

    cmd.extend([
        "-c:a", "aac" if codec != "copy" else "copy",
        "-avoid_negative_ts", "make_zero",
        "-y",
        str(output_path),
    ])

    logger.debug(f"提取切片: {start:.1f}s-{end:.1f}s → {output_path.name}")

    try:
        # 重编码比 stream copy 慢很多，需要更长超时
        timeout = 300 if codec != "copy" else 120
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        raise FFmpegError(f"FFmpeg 切片提取超时: {video_path}") from e
    except FileNotFoundError as e:
        raise FFmpegError("FFmpeg 未安装") from e

    if result.returncode != 0:
        raise FFmpegError(
            f"FFmpeg 切片提取失败 [{start:.1f}-{end:.1f}s] "
            f"(exit {result.returncode}): {result.stderr}"
        )

    if not output_path.exists():
        raise FFmpegError(f"FFmpeg 切片提取后文件不存在: {output_path}")

    return output_path
