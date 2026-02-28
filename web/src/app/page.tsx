import { Suspense } from "react";
import Link from "next/link";
import { Scissors, Settings } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { UploadZone } from "@/components/upload-zone";
import { ProjectList } from "@/components/project-list";
import { GlobalClipSearch } from "@/components/global-clip-search";
import { HomeTabs } from "@/components/home-tabs";
import { StatsOverview } from "@/components/stats-overview";

function ProjectListSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="space-y-3">
          <Skeleton className="aspect-video w-full rounded-lg" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      ))}
    </div>
  );
}

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card shadow-sm">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-3 px-6">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-primary/10 p-2">
              <Scissors className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">DeepCut</h1>
              <p className="text-xs text-muted-foreground">智能短视频切片系统</p>
            </div>
          </div>
          <div className="ml-auto">
            <Link
              href="/settings"
              aria-label="设置"
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              <Settings className="h-4 w-4" />
              <span className="hidden sm:inline">设置</span>
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8 space-y-8">
        {/* 统计概览 */}
        <section>
          <h2 className="text-lg font-semibold text-foreground mb-4">数据概览</h2>
          <StatsOverview />
        </section>

        <Separator />

        {/* 视频输入区 */}
        <section>
          <h2 className="text-lg font-semibold text-foreground mb-4">新建切片任务</h2>
          <UploadZone />
        </section>

        <Separator />

        {/* 双 Tab: 按项目 / 全局片段库 */}
        <HomeTabs
          projectsTab={
            <Suspense fallback={<ProjectListSkeleton />}>
              <ProjectList />
            </Suspense>
          }
          clipsTab={<GlobalClipSearch />}
        />
      </main>
    </div>
  );
}
