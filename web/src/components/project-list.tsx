import { prisma } from "@/lib/prisma";
import { ProjectCard } from "./project-card";
import { Scissors } from "lucide-react";

interface ProjectListProps {
  status?: string;
}

export async function ProjectList({ status }: ProjectListProps) {
  const where =
    status && status !== "all"
      ? { status: status as "pending" | "processing" | "completed" | "failed" }
      : {};

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

  if (projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <Scissors className="h-12 w-12 mb-3 opacity-40" />
        <p className="text-sm">暂无项目，上传视频开始切片</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {projects.map((p) => (
        <ProjectCard
          key={p.id}
          id={p.id}
          name={p.name}
          status={p.status}
          totalClips={p.totalClips}
          elapsed={p.elapsed}
          createdAt={p.createdAt.toISOString()}
          thumbnailUrl={
            p.clips[0]?.thumbnailPath
              ? `/api/projects/${p.id}/clips/0/thumbnail`
              : null
          }
        />
      ))}
    </div>
  );
}
