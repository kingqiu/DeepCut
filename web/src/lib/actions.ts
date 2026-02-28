"use server";

import { revalidatePath } from "next/cache";
import { prisma } from "./prisma";
import { processQueue, type ProcessJobData } from "./queue";

/** 创建项目并提交切片任务 */
export async function createProject(formData: FormData): Promise<{
  success: boolean;
  projectId?: string;
  error?: string;
}> {
  try {
    const videoPath = formData.get("videoPath") as string;
    const name = formData.get("name") as string | null;

    if (!videoPath) {
      return { success: false, error: "视频路径不能为空" };
    }

    const project = await prisma.project.create({
      data: {
        name: name || videoPath.split("/").pop() || "未命名",
        source: "upload",
        sourcePath: videoPath,
        status: "pending",
      },
    });

    await processQueue.add("process", {
      projectId: project.id,
      videoPath,
    } satisfies ProcessJobData);

    revalidatePath("/");
    return { success: true, projectId: project.id };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { success: false, error: message };
  }
}

/** 从本地路径创建项目 */
export async function createProjectFromPath(
  videoPath: string,
  outputDir?: string
): Promise<{ success: boolean; projectId?: string; error?: string }> {
  try {
    const project = await prisma.project.create({
      data: {
        name: videoPath.split("/").pop() || "未命名",
        source: "upload",
        sourcePath: videoPath,
        status: "pending",
      },
    });

    await processQueue.add("process", {
      projectId: project.id,
      videoPath,
      outputDir,
    } satisfies ProcessJobData);

    revalidatePath("/");
    return { success: true, projectId: project.id };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { success: false, error: message };
  }
}

/** 获取项目列表 */
export async function getProjects(status?: string): Promise<
  Array<{
    id: string;
    name: string;
    source: string;
    status: string;
    totalClips: number;
    elapsed: number | null;
    createdAt: Date;
    thumbnailPath: string | null;
  }>
> {
  const where = status && status !== "all" ? { status: status as "pending" | "processing" | "completed" | "failed" } : {};

  const projects = await prisma.project.findMany({
    where,
    orderBy: { createdAt: "desc" },
    include: {
      clips: {
        where: { index: 0 },
        select: { thumbnailPath: true },
        take: 1,
      },
    },
  });

  return projects.map((p) => ({
    id: p.id,
    name: p.name,
    source: p.source,
    status: p.status,
    totalClips: p.totalClips,
    elapsed: p.elapsed,
    createdAt: p.createdAt,
    thumbnailPath: p.clips[0]?.thumbnailPath ?? null,
  }));
}

/** 获取项目详情（含所有切片） */
export async function getProjectDetail(projectId: string) {
  const project = await prisma.project.findUnique({
    where: { id: projectId },
    include: {
      clips: {
        orderBy: { index: "asc" },
        include: {
          tags: true,
          relationships: true,
        },
      },
    },
  });

  return project;
}

/** 全局片段搜索（跨项目按标签筛选） */
export async function searchClips(filters: {
  dimensions?: Record<string, string[]>;
  keyword?: string;
  limit?: number;
  offset?: number;
}): Promise<{
  clips: Array<{
    id: string;
    index: number;
    start: number;
    end: number;
    duration: number;
    fileName: string;
    thumbnailPath: string;
    topic: string;
    summary: string;
    orientation: string;
    projectId: string;
    projectName: string;
    tags: Array<{ dimension: string; value: string }>;
  }>;
  total: number;
}> {
  const { dimensions, keyword, limit = 20, offset = 0 } = filters;

  // 构建 where 条件
  const where: Record<string, unknown> = {};
  const andConditions: Array<Record<string, unknown>> = [];

  // 标签维度筛选
  if (dimensions) {
    for (const [dimension, values] of Object.entries(dimensions)) {
      if (values.length > 0) {
        andConditions.push({
          tags: {
            some: {
              dimension,
              value: { in: values },
            },
          },
        });
      }
    }
  }

  // 关键词搜索（搜转录文本和话题）
  if (keyword) {
    andConditions.push({
      OR: [
        { transcriptText: { contains: keyword, mode: "insensitive" } },
        { topic: { contains: keyword, mode: "insensitive" } },
        { summary: { contains: keyword, mode: "insensitive" } },
      ],
    });
  }

  if (andConditions.length > 0) {
    where.AND = andConditions;
  }

  const [clips, total] = await Promise.all([
    prisma.clip.findMany({
      where,
      orderBy: { createdAt: "desc" },
      skip: offset,
      take: limit,
      include: {
        tags: true,
        project: { select: { id: true, name: true } },
      },
    }),
    prisma.clip.count({ where }),
  ]);

  return {
    clips: clips.map((c) => ({
      id: c.id,
      index: c.index,
      start: c.start,
      end: c.end,
      duration: c.duration,
      fileName: c.fileName,
      thumbnailPath: c.thumbnailPath,
      topic: c.topic,
      summary: c.summary,
      orientation: c.orientation,
      projectId: c.project.id,
      projectName: c.project.name,
      tags: c.tags.map((t) => ({ dimension: t.dimension, value: t.value })),
    })),
    total,
  };
}

/** 获取所有标签（用于筛选面板） */
export async function getAllTags(): Promise<
  Record<string, string[]>
> {
  const tags = await prisma.clipTag.findMany({
    select: { dimension: true, value: true },
    distinct: ["dimension", "value"],
    orderBy: [{ dimension: "asc" }, { value: "asc" }],
  });

  const result: Record<string, string[]> = {};
  for (const tag of tags) {
    if (!result[tag.dimension]) {
      result[tag.dimension] = [];
    }
    result[tag.dimension].push(tag.value);
  }
  return result;
}
