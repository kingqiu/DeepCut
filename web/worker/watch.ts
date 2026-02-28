/**
 * 本地目录监听 Worker
 *
 * 定期扫描 WatchDir 配置的目录，发现新视频文件自动创建项目并入队处理
 *
 * 启动方式:
 *   npx tsx worker/watch.ts
 */

import "dotenv/config";
import * as fs from "node:fs/promises";
import * as path from "node:path";
import { PrismaClient } from "@prisma/client";
import { Queue } from "bullmq";

interface ProcessJobData {
  projectId: string;
  videoPath: string;
}

const redisUrl = new URL(process.env.REDIS_URL ?? "redis://localhost:6379");
const redisConnection = {
  host: redisUrl.hostname,
  port: Number(redisUrl.port || 6379),
};

const prisma = new PrismaClient();
const processQueue = new Queue("deepcut-process", { connection: redisConnection });

const VIDEO_EXTENSIONS = new Set([
  ".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm", ".ts", ".m4v",
]);

async function scanDirectory(dirPath: string): Promise<string[]> {
  const videos: string[] = [];
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase();
        if (VIDEO_EXTENSIONS.has(ext)) {
          videos.push(path.join(dirPath, entry.name));
        }
      }
    }
  } catch (err) {
    console.error(`[Watch] 扫描目录失败: ${dirPath}`, err);
  }
  return videos;
}

async function processWatchDir(dir: {
  id: string;
  path: string;
  processedFiles: string[];
}): Promise<number> {
  const videos = await scanDirectory(dir.path);
  const processed = new Set(dir.processedFiles);
  const newVideos = videos.filter((v) => !processed.has(v));

  if (newVideos.length === 0) return 0;

  console.log(`[Watch] ${dir.path}: 发现 ${newVideos.length} 个新视频`);

  for (const videoPath of newVideos) {
    const name = path.basename(videoPath);

    const project = await prisma.project.create({
      data: {
        name,
        source: "local_watch",
        sourcePath: videoPath,
        status: "pending",
        watchDirId: dir.id,
      },
    });

    await processQueue.add("process", {
      projectId: project.id,
      videoPath,
    } satisfies ProcessJobData);

    console.log(`[Watch] 入队: ${name} → ${project.id}`);
  }

  // 更新已处理文件列表
  await prisma.watchDir.update({
    where: { id: dir.id },
    data: {
      processedFiles: [...dir.processedFiles, ...newVideos],
      lastScan: new Date(),
    },
  });

  return newVideos.length;
}

async function runScanCycle(): Promise<void> {
  const dirs = await prisma.watchDir.findMany({
    where: { enabled: true },
  });

  if (dirs.length === 0) return;

  let totalNew = 0;
  for (const dir of dirs) {
    totalNew += await processWatchDir(dir);
  }

  if (totalNew > 0) {
    console.log(`[Watch] 本轮扫描完成: ${totalNew} 个新视频入队`);
  }
}

// 主循环：每 30 秒检查一次是否有目录需要扫描
const CHECK_INTERVAL = 30_000; // 30s

async function main(): Promise<void> {
  console.log("[Watch] 目录监听 Worker 已启动");

  // 记录每个目录的上次扫描时间
  const lastScanMap = new Map<string, number>();

  while (true) {
    try {
      const dirs = await prisma.watchDir.findMany({
        where: { enabled: true },
      });

      for (const dir of dirs) {
        const lastScan = lastScanMap.get(dir.id) ?? 0;
        const now = Date.now();

        if (now - lastScan >= dir.interval * 1000) {
          await processWatchDir(dir);
          lastScanMap.set(dir.id, now);
        }
      }
    } catch (err) {
      console.error("[Watch] 扫描异常:", err);
    }

    await new Promise((r) => setTimeout(r, CHECK_INTERVAL));
  }
}

main().catch(console.error);
