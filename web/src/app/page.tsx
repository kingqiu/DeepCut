import { Suspense } from "react";
import Link from "next/link";
import { Scissors, Settings } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { UploadZone } from "@/components/upload-zone";
import { ProjectList } from "@/components/project-list";
import { GlobalClipSearch } from "@/components/global-clip-search";
import { HomeTabs } from "@/components/home-tabs";
import { getAllTags } from "@/lib/actions";

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

export default async function HomePage() {
  const allTags = await getAllTags();

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-2 px-4">
          <Scissors className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold">DeepCut</h1>
          <span className="text-sm text-muted-foreground">智能短视频切片</span>
          <div className="ml-auto">
            <Link href="/settings" aria-label="设置">
              <Settings className="h-5 w-5 text-muted-foreground hover:text-foreground transition-colors" />
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 space-y-6">
        {/* 视频输入区 */}
        <section>
          <h2 className="text-sm font-medium text-muted-foreground mb-3">新建切片任务</h2>
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
          clipsTab={<GlobalClipSearch allTags={allTags} />}
        />
      </main>
    </div>
  );
}
