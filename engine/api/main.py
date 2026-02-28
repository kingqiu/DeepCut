"""DeepCut FastAPI 应用入口

启动方式:
    cd engine
    .venv/bin/uvicorn api.main:app --reload --port 8000
"""

import json
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from loguru import logger

from api.job_store import job_store
from api.models import JobCreateRequest, JobCreateResponse, JobStatus

app = FastAPI(
    title="DeepCut API",
    description="智能短视频切片引擎 HTTP API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _run_pipeline(job_id: str, req: JobCreateRequest) -> None:
    """后台线程执行切片流水线"""
    from deepcut.config import DeepCutConfig
    from deepcut.pipeline.orchestrator import PipelineOrchestrator

    job_store.update(job_id, status="running", progress="初始化流水线")
    t0 = time.monotonic()

    try:
        config = DeepCutConfig()

        if req.min_duration != 5.0:
            config.deepcut_default_min_duration = req.min_duration
        if req.max_duration != 60.0:
            config.deepcut_default_max_duration = req.max_duration

        # 输出目录：优先用请求指定的，否则用 STORAGE_ROOT/output/
        if req.output_dir:
            output_dir = Path(req.output_dir)
        else:
            output_dir = config.deepcut_storage_root / "output"

        project_id = req.project_id or None

        orchestrator = PipelineOrchestrator(
            config=config,
            disable_motion=req.disable_motion,
            disable_speech=req.disable_speech,
        )

        job_store.update(job_id, progress="流水线运行中")
        version_dir = orchestrator.run(
            Path(req.video_path),
            output_dir=output_dir,
            project_id=project_id,
        )

        # 读取 metadata 获取切片数
        metadata_path = version_dir / "metadata.json"
        total_clips = 0
        if metadata_path.exists():
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            total_clips = len(data.get("clips", []))

        elapsed = time.monotonic() - t0
        job_store.update(
            job_id,
            status="completed",
            progress="切片完成",
            version_dir=str(version_dir),
            total_clips=total_clips,
            elapsed=round(elapsed, 1),
        )
        logger.info(f"任务完成: {job_id}, {total_clips} 切片, {elapsed:.1f}s")

    except Exception as e:
        elapsed = time.monotonic() - t0
        job_store.update(
            job_id,
            status="failed",
            progress="切片失败",
            error=str(e),
            elapsed=round(elapsed, 1),
        )
        logger.error(f"任务失败: {job_id}, {e}")


# ---- API 路由 ----


@app.post("/api/jobs", response_model=JobCreateResponse)
def create_job(req: JobCreateRequest) -> JobCreateResponse:
    """提交切片任务"""
    video_path = Path(req.video_path)
    if not video_path.exists():
        raise HTTPException(status_code=400, detail=f"视频文件不存在: {req.video_path}")

    job = job_store.create(req.video_path, req.output_dir)

    thread = threading.Thread(
        target=_run_pipeline,
        args=(job.job_id, req),
        daemon=True,
    )
    thread.start()

    return JobCreateResponse(
        job_id=job.job_id,
        status="pending",
        message="任务已提交，后台处理中",
    )


@app.get("/api/jobs", response_model=list[JobStatus])
def list_jobs() -> list[JobStatus]:
    """列出所有任务"""
    return job_store.list_all()


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
def get_job(job_id: str) -> JobStatus:
    """查询任务状态"""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return job


@app.get("/api/jobs/{job_id}/result")
def get_result(job_id: str) -> dict:
    """获取切片结果（metadata.json 内容）"""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail=f"任务状态: {job.status}，尚未完成")

    metadata_path = Path(job.version_dir) / "metadata.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="metadata.json 不存在")

    return json.loads(metadata_path.read_text(encoding="utf-8"))


@app.get("/api/jobs/{job_id}/clips/{index}/thumbnail")
def get_thumbnail(job_id: str, index: int) -> FileResponse:
    """获取切片缩略图"""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="任务尚未完成")

    thumb_path = Path(job.version_dir) / "thumbnails" / f"thumb_{index:03d}.jpg"
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail=f"缩略图不存在: clip_{index}")

    return FileResponse(thumb_path, media_type="image/jpeg")


@app.get("/api/jobs/{job_id}/clips/{index}/video")
def get_clip_video(job_id: str, index: int) -> FileResponse:
    """下载切片视频"""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="任务尚未完成")

    clip_path = Path(job.version_dir) / "clips" / f"clip_{index:03d}.mp4"
    if not clip_path.exists():
        raise HTTPException(status_code=404, detail=f"切片视频不存在: clip_{index}")

    return FileResponse(
        clip_path,
        media_type="video/mp4",
        filename=f"clip_{index:03d}.mp4",
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    """健康检查"""
    return {"status": "ok", "service": "deepcut-api"}
