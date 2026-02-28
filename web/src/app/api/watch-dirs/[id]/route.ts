import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
): Promise<NextResponse> {
  const { id } = await params;

  try {
    const body = (await request.json()) as {
      enabled?: boolean;
      interval?: number;
    };

    const dir = await prisma.watchDir.update({
      where: { id },
      data: {
        ...(body.enabled !== undefined && { enabled: body.enabled }),
        ...(body.interval !== undefined && { interval: body.interval }),
      },
    });

    return NextResponse.json(dir);
  } catch {
    return NextResponse.json({ error: "更新失败" }, { status: 500 });
  }
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
): Promise<NextResponse> {
  const { id } = await params;

  try {
    await prisma.watchDir.delete({ where: { id } });
    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ error: "删除失败" }, { status: 500 });
  }
}
