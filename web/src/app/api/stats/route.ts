import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  try {
    const [totalProjects, processing, completed, totalClipsResult] = await Promise.all([
      prisma.project.count(),
      prisma.project.count({ where: { status: "processing" } }),
      prisma.project.count({ where: { status: "completed" } }),
      prisma.project.aggregate({
        _sum: {
          totalClips: true,
        },
      }),
    ]);

    return NextResponse.json({
      totalProjects,
      processing,
      completed,
      totalClips: totalClipsResult._sum.totalClips || 0,
    });
  } catch (error) {
    console.error("Failed to fetch stats:", error);
    return NextResponse.json(
      { error: "Failed to fetch stats" },
      { status: 500 }
    );
  }
}
