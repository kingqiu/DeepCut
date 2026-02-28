"""API 请求/响应数据模型"""

from typing import Literal

from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    """创建切片任务请求"""

    video_path: str = Field(description="视频文件绝对路径")
    output_dir: str = Field(default="", description="输出目录（空则使用 DEEPCUT_STORAGE_ROOT/output/）")
    project_id: str = Field(default="", description="Web 项目 ID（用于统一存储路径）")
    min_duration: float = Field(default=5.0, description="最小切片时长（秒）")
    max_duration: float = Field(default=60.0, description="最大切片时长（秒）")
    disable_motion: bool = Field(default=False, description="禁用运镜检测")
    disable_speech: bool = Field(default=False, description="禁用语音分析")


class JobStatus(BaseModel):
    """任务状态"""

    job_id: str
    status: Literal["pending", "running", "completed", "failed"]
    progress: str = Field(default="", description="当前进度描述")
    video_path: str = ""
    output_dir: str = ""
    version_dir: str = ""
    total_clips: int = 0
    elapsed: float = 0.0
    error: str = ""


class JobCreateResponse(BaseModel):
    """创建任务响应"""

    job_id: str
    status: Literal["pending", "running", "completed", "failed"]
    message: str
