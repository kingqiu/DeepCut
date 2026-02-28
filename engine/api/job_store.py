"""任务存储：内存级任务管理（MVP 阶段，后续迁移到 Redis/PostgreSQL）"""

import time
import uuid
from typing import Literal

from loguru import logger

from api.models import JobStatus


class JobStore:
    """内存任务存储

    线程安全由 GIL 保证（MVP 够用），后续可替换为 Redis。
    """

    def __init__(self) -> None:
        self._jobs: dict[str, JobStatus] = {}

    def create(self, video_path: str, output_dir: str) -> JobStatus:
        job_id = uuid.uuid4().hex[:12]
        job = JobStatus(
            job_id=job_id,
            status="pending",
            progress="等待处理",
            video_path=video_path,
            output_dir=output_dir,
        )
        self._jobs[job_id] = job
        logger.info(f"任务创建: {job_id} → {video_path}")
        return job

    def get(self, job_id: str) -> JobStatus | None:
        return self._jobs.get(job_id)

    def update(
        self,
        job_id: str,
        *,
        status: Literal["pending", "running", "completed", "failed"] | None = None,
        progress: str | None = None,
        version_dir: str | None = None,
        total_clips: int | None = None,
        elapsed: float | None = None,
        error: str | None = None,
    ) -> None:
        job = self._jobs.get(job_id)
        if not job:
            return
        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if version_dir is not None:
            job.version_dir = version_dir
        if total_clips is not None:
            job.total_clips = total_clips
        if elapsed is not None:
            job.elapsed = elapsed
        if error is not None:
            job.error = error

    def list_all(self) -> list[JobStatus]:
        return list(self._jobs.values())


# 全局单例
job_store = JobStore()
