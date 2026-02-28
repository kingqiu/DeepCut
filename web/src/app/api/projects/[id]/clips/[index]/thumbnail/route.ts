import { NextRequest, NextResponse } from "next/server";
import { readFile } from "fs/promises";
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

  const thumbPath = join(project.versionDir, "thumbnails", `thumb_${String(clipIndex).padStart(3, "0")}.jpg`);

  try {
    const data = await readFile(thumbPath);
    return new NextResponse(data, {
      headers: { "Content-Type": "image/jpeg", "Cache-Control": "public, max-age=86400" },
    });
  } catch {
    return NextResponse.json({ error: "缩略图不存在" }, { status: 404 });
  }
}
