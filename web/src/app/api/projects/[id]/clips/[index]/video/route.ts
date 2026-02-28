import { NextRequest, NextResponse } from "next/server";
import { readFile, stat } from "fs/promises";
import { join } from "path";
import { prisma } from "@/lib/prisma";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string; index: string }> }
): Promise<NextResponse> {
  const { id, index } = await params;
  const clipIndex = parseInt(index, 10);

  const project = await prisma.project.findUnique({
    where: { id },
    select: { versionDir: true },
  });

  if (!project?.versionDir) {
    return NextResponse.json({ error: "项目不存在或未完成" }, { status: 404 });
  }

  const clipPath = join(project.versionDir, "clips", `clip_${String(clipIndex).padStart(3, "0")}.mp4`);

  try {
    const fileStat = await stat(clipPath);
    const data = await readFile(clipPath);
    return new NextResponse(data, {
      headers: {
        "Content-Type": "video/mp4",
        "Content-Length": String(fileStat.size),
        "Content-Disposition": `attachment; filename="clip_${String(clipIndex).padStart(3, "0")}.mp4"`,
      },
    });
  } catch {
    return NextResponse.json({ error: "切片视频不存在" }, { status: 404 });
  }
}
