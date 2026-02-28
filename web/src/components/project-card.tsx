"use client";

import Link from "next/link";
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

export function ProjectCard({
  id,
  name,
  status,
  totalClips,
  elapsed,
  createdAt,
  thumbnailUrl,
}: ProjectCardProps) {
  const statusConf = STATUS_CONFIG[status];

  return (
    <Link href={`/projects/${id}`}>
      <Card className="group cursor-pointer overflow-hidden transition-shadow hover:shadow-md">
        {/* 缩略图区域 */}
        <div className="relative aspect-video bg-muted">
          {thumbnailUrl ? (
            <img
              src={thumbnailUrl}
              alt={name}
              className="h-full w-full object-cover"
            />
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
                    {elapsed.toFixed(0)}s
                  </span>
                )}
              </>
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
