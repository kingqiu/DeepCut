"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Film, Clock, Scissors, AlertCircle, Loader2, CheckCircle2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PROJECT_STATUS_LABELS, type ProjectStatus } from "@/types";

interface ProjectCardProps {
  id: string;
  name: string;
  status: ProjectStatus;
  totalClips: number;
  elapsed: number | null;
  createdAt: string;
  thumbnailUrl: string | null;
}

const STATUS_CONFIG: Record<
  ProjectStatus,
  { icon: React.ReactNode; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  pending: { icon: <Clock className="h-3 w-3" />, variant: "secondary" },
  processing: { icon: <Loader2 className="h-3 w-3 animate-spin" />, variant: "outline" },
  completed: { icon: <CheckCircle2 className="h-3 w-3" />, variant: "default" },
  failed: { icon: <AlertCircle className="h-3 w-3" />, variant: "destructive" },
};

function formatElapsed(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}m${s}s`;
}

export function ProjectCard({
  id,
  name,
  status: initialStatus,
  totalClips: initialClips,
  elapsed: initialElapsed,
  createdAt,
  thumbnailUrl,
}: ProjectCardProps) {
  const router = useRouter();
  const [status, setStatus] = useState<ProjectStatus>(initialStatus);
  const [totalClips, setTotalClips] = useState(initialClips);
  const [elapsed, setElapsed] = useState(initialElapsed);
  const [elapsedLive, setElapsedLive] = useState(0);
  const startTimeRef = useRef(Date.now());

  // 实时轮询 pending/processing 状态
  useEffect(() => {
    if (status !== "pending" && status !== "processing") return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/projects/${id}/status`);
        if (!res.ok) return;
        const data = await res.json();
        setStatus(data.status);
        setTotalClips(data.totalClips);
        setElapsed(data.elapsed);

        if (data.status === "completed" || data.status === "failed") {
          clearInterval(interval);
          // 刷新 Server Component 数据（缩略图等）
          router.refresh();
        }
      } catch {
        // 忽略轮询错误
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [id, status, router]);

  // 实时计时器
  useEffect(() => {
    if (status !== "pending" && status !== "processing") return;
    startTimeRef.current = Date.now();

    const timer = setInterval(() => {
      setElapsedLive(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);

    return () => clearInterval(timer);
  }, [status]);

  const statusConf = STATUS_CONFIG[status];
  const isActive = status === "pending" || status === "processing";

  return (
    <Link href={`/projects/${id}`}>
      <Card className={`group cursor-pointer overflow-hidden transition-shadow hover:shadow-md ${
        isActive ? "ring-2 ring-primary/20" : ""
      }`}>
        {/* 缩略图区域 */}
        <div className="relative aspect-video bg-muted">
          {status === "completed" && thumbnailUrl ? (
            <img
              src={thumbnailUrl}
              alt={name}
              width={640}
              height={360}
              className="h-full w-full object-cover"
            />
          ) : isActive ? (
            <div className="flex h-full flex-col items-center justify-center gap-2">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-xs text-muted-foreground">
                {status === "pending" ? "排队中…" : "正在切片…"}
              </p>
              <p className="text-xs font-mono text-muted-foreground/60">
                {formatElapsed(elapsedLive)}
              </p>
            </div>
          ) : (
            <div className="flex h-full items-center justify-center">
              <Film className="h-10 w-10 text-muted-foreground/40" />
            </div>
          )}
          <Badge
            variant={statusConf.variant}
            className="absolute right-2 top-2 gap-1"
          >
            {statusConf.icon}
            {PROJECT_STATUS_LABELS[status]}
          </Badge>
        </div>

        <CardContent className="p-3">
          <h3 className="truncate text-sm font-medium group-hover:text-primary">
            {name}
          </h3>
          <div className="mt-1.5 flex items-center gap-3 text-xs text-muted-foreground">
            {status === "completed" && (
              <>
                <span className="flex items-center gap-1">
                  <Scissors className="h-3 w-3" />
                  {totalClips} 切片
                </span>
                {elapsed != null && (
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatElapsed(elapsed)}
                  </span>
                )}
              </>
            )}
            {status === "failed" && (
              <span className="text-destructive">处理失败</span>
            )}
            <span className="ml-auto">
              {new Date(createdAt).toLocaleDateString("zh-CN", {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
