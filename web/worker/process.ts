/**
 * BullMQ Worker: 切片处理
 *
 * 从队列取任务 → 调用 Python Engine FastAPI → 解析结果写入 PostgreSQL
 *
 * 启动方式:
 *   npx tsx worker/process.ts
 */

import "dotenv/config";
import { Worker, Job } from "bullmq";
import { PrismaClient } from "@prisma/client";

interface ProcessJobData {
  projectId: string;
  videoPath: string;
  outputDir?: string;
  minDuration?: number;
  maxDuration?: number;
  disableMotion?: boolean;
  disableSpeech?: boolean;
}

const redisUrl = new URL(process.env.REDIS_URL ?? "redis://localhost:6379");
const redisConnection = {
  host: redisUrl.hostname,
  port: Number(redisUrl.port || 6379),
};

const ENGINE_API_URL = process.env.ENGINE_API_URL ?? "http://localhost:8080";
const prisma = new PrismaClient();

async function processJob(job: Job<ProcessJobData>): Promise<void> {
  const { projectId, videoPath, outputDir, minDuration, maxDuration, disableMotion, disableSpeech } = job.data;

  console.log(`[Worker] 开始处理: ${projectId} → ${videoPath}`);

  await prisma.project.update({
    where: { id: projectId },
    data: { status: "processing" },
  });

  try {
    // 1. 提交任务到 Engine API
    const submitRes = await fetch(`${ENGINE_API_URL}/api/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        video_path: videoPath,
        output_dir: outputDir ?? "",
        min_duration: minDuration ?? 5.0,
        max_duration: maxDuration ?? 60.0,
        disable_motion: disableMotion ?? false,
        disable_speech: disableSpeech ?? false,
      }),
    });

    if (!submitRes.ok) {
      const err = await submitRes.text();
      throw new Error(`Engine API 提交失败: ${submitRes.status} ${err}`);
    }

    const { job_id: engineJobId } = (await submitRes.json()) as { job_id: string };
    console.log(`[Worker] Engine job: ${engineJobId}`);

    // 2. 轮询 Engine 任务状态
    const result = await pollEngineJob(engineJobId);

    // 3. 获取完整 metadata
    const metaRes = await fetch(`${ENGINE_API_URL}/api/jobs/${engineJobId}/result`);
    if (!metaRes.ok) {
      throw new Error(`获取 metadata 失败: ${metaRes.status}`);
    }
    const metadata = (await metaRes.json()) as EngineMetadata;

    // 4. 写入数据库
    await saveResultToDb(projectId, result, metadata);

    console.log(`[Worker] 完成: ${projectId}, ${result.total_clips} 切片, ${result.elapsed}s`);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(`[Worker] 失败: ${projectId}, ${message}`);
    await prisma.project.update({
      where: { id: projectId },
      data: { status: "failed", error: message },
    });
    throw err;
  }
}

interface EngineJobStatus {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: string;
  version_dir: string;
  total_clips: number;
  elapsed: number;
  error: string;
}

interface EngineClipMeta {
  index: number;
  start: number;
  end: number;
  duration: number;
  file_name: string;
  file_path: string;
  thumbnail: string;
  split_reason: string;
  scene_group: number;
  orientation: string;
  transcript_segment: string;
  topic: string;
  summary: string;
  tags: {
    tags: Array<{ dimension: string; values: string[] }>;
  };
  relationships: Array<{
    related_index: number;
    relationship_type: string;
  }>;
}

interface EngineMetadata {
  video_info: Record<string, unknown>;
  clips: EngineClipMeta[];
}

async function pollEngineJob(engineJobId: string): Promise<EngineJobStatus> {
  const POLL_INTERVAL = 5000;
  const MAX_POLL_TIME = 600_000; // 10 min
  const start = Date.now();

  while (Date.now() - start < MAX_POLL_TIME) {
    const res = await fetch(`${ENGINE_API_URL}/api/jobs/${engineJobId}`);
    if (!res.ok) throw new Error(`轮询失败: ${res.status}`);

    const status = (await res.json()) as EngineJobStatus;

    if (status.status === "completed") return status;
    if (status.status === "failed") throw new Error(`Engine 处理失败: ${status.error}`);

    await new Promise((r) => setTimeout(r, POLL_INTERVAL));
  }

  throw new Error("Engine 处理超时 (10min)");
}

async function saveResultToDb(
  projectId: string,
  result: EngineJobStatus,
  metadata: EngineMetadata
): Promise<void> {
  await prisma.$transaction(async (tx) => {
    await tx.project.update({
      where: { id: projectId },
      data: {
        status: "completed",
        versionDir: result.version_dir,
        totalClips: result.total_clips,
        elapsed: result.elapsed,
        videoMeta: metadata.video_info as object,
      },
    });

    for (const clipMeta of metadata.clips) {
      const clip = await tx.clip.create({
        data: {
          projectId,
          index: clipMeta.index,
          start: clipMeta.start,
          end: clipMeta.end,
          duration: clipMeta.duration,
          fileName: clipMeta.file_name,
          filePath: clipMeta.file_path ?? "",
          thumbnailPath: clipMeta.thumbnail ?? "",
          splitReason: clipMeta.split_reason,
          sceneGroup: clipMeta.scene_group,
          orientation: clipMeta.orientation,
          transcriptText: clipMeta.transcript_segment ?? "",
          topic: clipMeta.topic ?? "",
          summary: clipMeta.summary ?? "",
        },
      });

      // Tags: 每个维度每个值一行
      const tagRows: Array<{ clipId: string; dimension: string; value: string }> = [];
      if (clipMeta.tags?.tags) {
        for (const tag of clipMeta.tags.tags) {
          for (const value of tag.values) {
            tagRows.push({ clipId: clip.id, dimension: tag.dimension, value });
          }
        }
      }
      if (tagRows.length > 0) {
        await tx.clipTag.createMany({ data: tagRows });
      }

      // Relationships
      const relRows = clipMeta.relationships.map((rel) => ({
        clipId: clip.id,
        relatedClipIndex: rel.related_index,
        relationshipType: rel.relationship_type,
      }));
      if (relRows.length > 0) {
        await tx.clipRelationship.createMany({ data: relRows });
      }
    }
  });
}

// 启动 Worker
const worker = new Worker<ProcessJobData>("deepcut-process", processJob, {
  connection: redisConnection,
  concurrency: 1,
});

worker.on("completed", (job) => {
  console.log(`[Worker] Job ${job.id} completed`);
});

worker.on("failed", (job, err) => {
  console.error(`[Worker] Job ${job?.id} failed:`, err.message);
});

console.log("[Worker] DeepCut process worker started, waiting for jobs...");
