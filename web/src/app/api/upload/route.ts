import { NextRequest, NextResponse } from "next/server";
import { writeFile, mkdir } from "fs/promises";
import { join } from "path";
import { prisma } from "@/lib/prisma";
import { processQueue, type ProcessJobData } from "@/lib/queue";

const UPLOAD_DIR = process.env.UPLOAD_DIR ?? "/tmp/deepcut_uploads";
const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ error: "未选择文件" }, { status: 400 });
    }

    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { error: `文件超过 500MB 限制 (${(file.size / 1024 / 1024).toFixed(0)}MB)` },
        { status: 400 }
      );
    }

    // 确保上传目录存在
    await mkdir(UPLOAD_DIR, { recursive: true });

    // 生成唯一文件名
    const timestamp = Date.now();
    const safeName = file.name.replace(/[^a-zA-Z0-9._\u4e00-\u9fff-]/g, "_");
    const fileName = `${timestamp}_${safeName}`;
    const filePath = join(UPLOAD_DIR, fileName);

    // 写入文件
    const bytes = await file.arrayBuffer();
    await writeFile(filePath, Buffer.from(bytes));

    // 创建项目并入队
    const project = await prisma.project.create({
      data: {
        name: file.name,
        source: "upload",
        sourcePath: filePath,
        status: "pending",
      },
    });

    await processQueue.add("process", {
      projectId: project.id,
      videoPath: filePath,
    } satisfies ProcessJobData);

    return NextResponse.json({
      projectId: project.id,
      fileName: file.name,
      fileSize: file.size,
      message: "上传成功，已提交处理",
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("上传失败:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
