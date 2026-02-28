import { Suspense } from "react";
import { Scissors } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { UploadZone } from "@/components/upload-zone";
import { ProjectList } from "@/components/project-list";

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
      <header className="border-b">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-2 px-4">
          <Scissors className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold">DeepCut</h1>
          <span className="text-sm text-muted-foreground">智能短视频切片</span>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 space-y-6">
        {/* 视频输入区 */}
        <section>
          <h2 className="text-sm font-medium text-muted-foreground mb-3">新建切片任务</h2>
          <UploadZone />
        </section>

        <Separator />

        {/* 项目列表 */}
        <section>
          <h2 className="text-sm font-medium text-muted-foreground mb-3">项目列表</h2>
          <Suspense fallback={<ProjectListSkeleton />}>
            <ProjectList />
          </Suspense>
        </section>
      </main>
    </div>
  );
}
