import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Scissors, Clock, Film } from "lucide-react";
import { prisma } from "@/lib/prisma";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { PROJECT_STATUS_LABELS, type ProjectStatus } from "@/types";
import { ClipGrid } from "@/components/clip-grid";

interface ProjectPageProps {
  params: Promise<{ id: string }>;
}

export default async function ProjectPage({ params }: ProjectPageProps) {
  const { id } = await params;

  const project = await prisma.project.findUnique({
    where: { id },
    include: {
      clips: {
        orderBy: { index: "asc" },
        include: {
          tags: true,
          relationships: true,
        },
      },
    },
  });

  if (!project) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-2 px-4">
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-1">
              <ArrowLeft className="h-4 w-4" />
              返回
            </Button>
          </Link>
          <Separator orientation="vertical" className="h-6" />
          <Scissors className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold">DeepCut</h1>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 space-y-6">
        {/* 项目信息 */}
        <section className="space-y-2">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold">{project.name}</h2>
            <Badge variant={project.status === "completed" ? "default" : "secondary"}>
              {PROJECT_STATUS_LABELS[project.status as ProjectStatus]}
            </Badge>
          </div>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Film className="h-3.5 w-3.5" />
              {project.totalClips} 切片
            </span>
            {project.elapsed != null && (
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                处理耗时 {project.elapsed.toFixed(1)}s
              </span>
            )}
            <span>
              {project.createdAt.toLocaleDateString("zh-CN", {
                year: "numeric",
                month: "long",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
        </section>

        <Separator />

        {/* 切片网格 */}
        {project.status === "completed" && project.clips.length > 0 ? (
          <ClipGrid projectId={project.id} clips={project.clips} />
        ) : project.status === "processing" || project.status === "pending" ? (
          <div className="flex flex-col items-center py-16 text-muted-foreground">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <p className="mt-4 text-sm">正在处理中...</p>
          </div>
        ) : project.status === "failed" ? (
          <div className="flex flex-col items-center py-16 text-destructive">
            <p className="text-sm">处理失败: {project.error}</p>
          </div>
        ) : (
          <div className="flex flex-col items-center py-16 text-muted-foreground">
            <p className="text-sm">暂无切片数据</p>
          </div>
        )}
      </main>
    </div>
  );
}
