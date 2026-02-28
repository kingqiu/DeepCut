import { NextRequest, NextResponse } from "next/server";
import { writeFile, mkdir, access } from "fs/promises";
import { join } from "path";
import { prisma } from "@/lib/prisma";
import { processQueue, type ProcessJobData } from "@/lib/queue";

const UPLOAD_DIR = process.env.UPLOAD_DIR ?? "/tmp/deepcut_uploads";
const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

export async function POST(request: NextRequest): Promise<NextResponse> {
  const contentType = request.headers.get("content-type") ?? "";

  // JSON body → 本地路径提交
  if (contentType.includes("application/json")) {
    return handleLocalPath(request);
  }

  // multipart → 文件上传
  return handleFileUpload(request);
}

async function handleFileUpload(request: NextRequest): Promise<NextResponse> {
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

    await mkdir(UPLOAD_DIR, { recursive: true });

    const timestamp = Date.now();
    const safeName = file.name.replace(/[^a-zA-Z0-9._\u4e00-\u9fff-]/g, "_");
    const fileName = `${timestamp}_${safeName}`;
    const filePath = join(UPLOAD_DIR, fileName);

    const bytes = await file.arrayBuffer();
    await writeFile(filePath, Buffer.from(bytes));

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

async function handleLocalPath(request: NextRequest): Promise<NextResponse> {
  try {
    const body = (await request.json()) as { videoPath?: string };
    const videoPath = body.videoPath?.trim();

    if (!videoPath) {
      return NextResponse.json({ error: "视频路径不能为空" }, { status: 400 });
    }

    // 检查文件是否存在
    try {
      await access(videoPath);
    } catch {
      return NextResponse.json({ error: "文件不存在或无权限访问" }, { status: 400 });
    }

    const name = videoPath.split("/").pop() || "未命名";

    const project = await prisma.project.create({
      data: {
        name,
        source: "upload",
        sourcePath: videoPath,
        status: "pending",
      },
    });

    await processQueue.add("process", {
      projectId: project.id,
      videoPath,
    } satisfies ProcessJobData);

    return NextResponse.json({
      projectId: project.id,
      fileName: name,
      message: "已提交处理",
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("本地路径提交失败:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
