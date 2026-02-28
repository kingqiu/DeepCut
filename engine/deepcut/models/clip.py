"""切片相关数据模型"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class ClipPlan(BaseModel):
    """切片计划（Step 4 融合输出）"""

    index: int = Field(description="切片序号（从 0 开始）")
    start: float = Field(description="起始时间（秒）")
    end: float = Field(description="结束时间（秒）")
    split_reason: str = Field(description="切分原因")
    scene_group: int = Field(default=0, description="所属场景组")
    overlap_prev: float = Field(default=0.0, description="与前一片段重叠时长")
    overlap_next: float = Field(default=0.0, description="与后一片段重叠时长")
    topic: str = Field(default="", description="LLM 话题标题")
    summary: str = Field(default="", description="LLM 话题摘要")
    tags: "ClipTags | None" = Field(default=None, description="多维度标签")

    @property
    def duration(self) -> float:
        return self.end - self.start


class ClipTag(BaseModel):
    """切片标签（单个维度）"""

    dimension: Literal[
        "content", "emotion", "technical", "purpose",
        "scene", "object", "action",
    ] = Field(description="标签维度")
    values: list[str] = Field(description="该维度下的标签值列表")


class ClipTags(BaseModel):
    """切片多维度标签集合"""

    tags: list[ClipTag] = Field(default_factory=list)

    def get_dimension(self, dimension: str) -> list[str]:
        """获取指定维度的标签值"""
        for tag in self.tags:
            if tag.dimension == dimension:
                return tag.values
        return []


class ClipRelationship(BaseModel):
    """切片间关系"""

    related_index: int = Field(description="关联切片序号")
    relationship_type: Literal["sequence", "same_scene", "context_continuation"] = Field(
        description="关系类型"
    )


class ClipMetadata(BaseModel):
    """单个切片的完整元数据"""

    index: int
    start: float
    end: float
    duration: float
    file_name: str
    file_path: Path | None = None
    split_reason: str
    scene_group: int = 0
    overlap_prev: float = 0.0
    overlap_next: float = 0.0
    orientation: Literal["landscape", "portrait", "square"] = "landscape"
    tags: ClipTags = Field(default_factory=ClipTags)
    relationships: list[ClipRelationship] = Field(default_factory=list)
    transcript_segment: str = Field(default="", description="该切片对应的转录文本")
    topic: str = Field(default="", description="LLM 话题标题")
    summary: str = Field(default="", description="LLM 话题摘要")


class OutputMetadata(BaseModel):
    """切片版本完整输出元数据（metadata.json）"""

    version: str = Field(description="版本标签，如 v1_20260228_112300")
    source_video: str = Field(description="源视频路径")
    source_duration: float
    source_orientation: Literal["landscape", "portrait", "square"]
    total_clips: int
    config: dict[str, float | str | bool] = Field(
        default_factory=dict, description="本次切片使用的配置参数"
    )
    clips: list[ClipMetadata] = Field(default_factory=list)


# 解析前向引用（ClipPlan 中引用了 ClipTags）
ClipPlan.model_rebuild()
