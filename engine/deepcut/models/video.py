"""视频相关数据模型"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class VideoInfo(BaseModel):
    """视频基本信息（Step 1 预处理输出）"""

    path: Path
    duration: float = Field(description="时长（秒）")
    width: int
    height: int
    fps: float
    codec: str = Field(description="视频编码，如 h264, hevc, av1")
    audio_codec: str = Field(default="", description="音频编码，如 aac")
    has_audio: bool = Field(default=True, description="是否有音频轨")
    orientation: Literal["landscape", "portrait", "square"] = Field(
        description="画幅方向：横屏/竖屏/方形"
    )
    file_size: int = Field(description="文件大小（字节）")

    @property
    def aspect_ratio(self) -> float:
        """宽高比"""
        if self.height == 0:
            return 0.0
        return self.width / self.height
