"""视频处理工具函数：时间格式转换、文件命名等"""


def seconds_to_hms(seconds: float) -> str:
    """秒数转 HH:MM:SS.mmm 格式

    >>> seconds_to_hms(3661.5)
    '01:01:01.500'
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def hms_to_seconds(hms: str) -> float:
    """HH:MM:SS.mmm 或 HH:MM:SS,mmm 格式转秒数

    >>> hms_to_seconds('01:01:01.500')
    3661.5
    """
    normalized = hms.replace(",", ".")
    parts = normalized.split(":")
    if len(parts) != 3:
        raise ValueError(f"无效的时间格式: {hms}")

    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s


def format_duration(seconds: float) -> str:
    """格式化时长为人类可读格式

    >>> format_duration(65.5)
    '1m05s'
    >>> format_duration(3661.0)
    '1h01m01s'
    >>> format_duration(30.0)
    '30s'
    """
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}m{s:02d}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h}h{m:02d}m{s:02d}s"


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """清理文件名，移除不安全字符

    >>> sanitize_filename('测试/视频:名称')
    '测试_视频_名称'
    """
    unsafe_chars = r'<>:"/\|?*'
    result = name
    for char in unsafe_chars:
        result = result.replace(char, "_")
    result = result.strip(". ")
    if len(result) > max_length:
        result = result[:max_length]
    return result or "unnamed"
