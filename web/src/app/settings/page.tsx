import { Scissors, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { WatchDirManager } from "@/components/watch-dir-manager";

export default function SettingsPage() {
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
          <h1 className="text-lg font-semibold">设置</h1>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-6 space-y-8">
        <section>
          <h2 className="text-lg font-semibold mb-1">本地目录监听</h2>
          <p className="text-sm text-muted-foreground mb-4">
            配置本地视频目录，系统会定期扫描新增视频并自动处理
          </p>
          <WatchDirManager />
        </section>
      </main>
    </div>
  );
}
