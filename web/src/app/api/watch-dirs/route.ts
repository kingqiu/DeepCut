import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(): Promise<NextResponse> {
  const dirs = await prisma.watchDir.findMany({
    orderBy: { createdAt: "desc" },
    include: { _count: { select: { projects: true } } },
  });
  return NextResponse.json(dirs);
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = (await request.json()) as {
      path: string;
      interval?: number;
    };

    if (!body.path?.trim()) {
      return NextResponse.json({ error: "目录路径不能为空" }, { status: 400 });
    }

    const dir = await prisma.watchDir.create({
      data: {
        path: body.path.trim(),
        interval: body.interval ?? 600,
      },
    });

    return NextResponse.json(dir);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    if (message.includes("Unique constraint")) {
      return NextResponse.json({ error: "该目录已存在" }, { status: 409 });
    }
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
