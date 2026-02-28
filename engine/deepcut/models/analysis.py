"""分析器输出数据模型"""

from typing import Literal

from pydantic import BaseModel, Field


class TimeRange(BaseModel):
    """时间区间"""

    start: float = Field(description="起始时间（秒）")
    end: float = Field(description="结束时间（秒）")

    @property
    def duration(self) -> float:
        return self.end - self.start


class VADSegment(BaseModel):
    """人声活动区间"""

    start: float
    end: float
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class VADResult(BaseModel):
    """VAD 检测结果（Step 2 输出）"""

    has_speech: bool = Field(description="视频中是否包含人声")
    speech_ratio: float = Field(
        default=0.0, ge=0.0, le=1.0, description="人声占比"
    )
    segments: list[VADSegment] = Field(default_factory=list)


class SceneChange(BaseModel):
    """场景切换点"""

    timestamp: float = Field(description="切换时间点（秒）")
    scene_type: Literal["cut", "fade", "dissolve"] = Field(
        default="cut", description="切换类型"
    )


class MotionChange(BaseModel):
    """运镜变化点"""

    start: float
    end: float
    motion_type: Literal["static", "pan", "tilt", "zoom", "shake", "transition"] = Field(
        description="运镜类型：固定/平移/倾斜/推拉/抖动/突变"
    )
    intensity: float = Field(default=0.5, ge=0.0, le=1.0, description="运动强度")


class TranscriptSegment(BaseModel):
    """转录文本片段"""

    start: float
    end: float
    text: str
    language: str = Field(default="zh")


class TranscriptResult(BaseModel):
    """语音转录结果"""

    language: str = Field(default="zh")
    segments: list[TranscriptSegment] = Field(default_factory=list)

    @property
    def full_text(self) -> str:
        return " ".join(seg.text for seg in self.segments)


class TopicSegment(BaseModel):
    """话题分段（LLM 输出）"""

    start: float
    end: float
    topic: str = Field(description="话题主题")
    summary: str = Field(default="", description="话题摘要")


class AnalysisResult(BaseModel):
    """综合分析结果（Step 3A/3B 输出）"""

    vad: VADResult
    scenes: list[SceneChange] = Field(default_factory=list)
    motions: list[MotionChange] = Field(default_factory=list)
    transcript: TranscriptResult | None = None
    topics: list[TopicSegment] = Field(default_factory=list)
