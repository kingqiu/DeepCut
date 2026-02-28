import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  try {
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

    return NextResponse.json(result);
  } catch (error) {
    console.error("Failed to fetch tags:", error);
    return NextResponse.json({}, { status: 500 });
  }
}
