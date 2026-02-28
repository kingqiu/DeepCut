import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { dimensions, keyword, limit = 20, offset = 0 } = body;

    // 构建 where 条件
    const where: Record<string, unknown> = {};
    const andConditions: Array<Record<string, unknown>> = [];

    // 标签维度筛选
    if (dimensions) {
      for (const [dimension, values] of Object.entries(dimensions)) {
        if (Array.isArray(values) && values.length > 0) {
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

    return NextResponse.json({
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
    });
  } catch (error) {
    console.error("Failed to search clips:", error);
    return NextResponse.json(
      { error: "Failed to search clips" },
      { status: 500 }
    );
  }
}
