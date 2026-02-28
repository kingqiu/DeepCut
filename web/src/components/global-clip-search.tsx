"use client";

import { useState, useCallback, useTransition, useEffect } from "react";
import Link from "next/link";
import { Search, X, Play, Download, Clock, Film } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  TAG_DIMENSION_COLORS,
  TAG_DIMENSION_LABELS,
  type TagDimension,
} from "@/types";
import { searchClips } from "@/lib/actions";

interface ClipResult {
  id: string;
  index: number;
  start: number;
  end: number;
  duration: number;
  fileName: string;
  thumbnailPath: string;
  topic: string;
  summary: string;
  orientation: string;
  projectId: string;
  projectName: string;
  tags: Array<{ dimension: string; value: string }>;
}

interface GlobalClipSearchProps {}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function GlobalClipSearch({}: GlobalClipSearchProps) {
  const [allTags, setAllTags] = useState<Record<string, string[]>>({});
  const [keyword, setKeyword] = useState("");
  const [selectedTags, setSelectedTags] = useState<Record<string, Set<string>>>({});
  const [clips, setClips] = useState<ClipResult[]>([]);
  const [total, setTotal] = useState(0);
  const [searched, setSearched] = useState(false);
  const [isPending, startTransition] = useTransition();

  // 加载所有标签
  useEffect(() => {
    fetch("/api/tags")
      .then((res) => res.json())
      .then((tags: Record<string, string[]>) => {
        console.log("Loaded tags:", tags);
        setAllTags(tags);
      })
      .catch((error: Error) => {
        console.error("Failed to load tags:", error);
        setAllTags({});
      });
  }, []);

  const doSearch = useCallback(
    (kw: string, tags: Record<string, Set<string>>) => {
      startTransition(async () => {
        const dimensions: Record<string, string[]> = {};
        for (const [dim, vals] of Object.entries(tags)) {
          if (vals.size > 0) dimensions[dim] = Array.from(vals);
        }

        const result = await searchClips({
          keyword: kw || undefined,
          dimensions: Object.keys(dimensions).length > 0 ? dimensions : undefined,
          limit: 40,
        });

        setClips(result.clips);
        setTotal(result.total);
        setSearched(true);
      });
    },
    []
  );

  function toggleTag(dimension: string, value: string) {
    const nextTags = { ...selectedTags };
    if (!nextTags[dimension]) nextTags[dimension] = new Set();
    const set = new Set(nextTags[dimension]);
    if (set.has(value)) {
      set.delete(value);
    } else {
      set.add(value);
    }
    if (set.size === 0) {
      delete nextTags[dimension];
    } else {
      nextTags[dimension] = set;
    }
    setSelectedTags(nextTags);
    doSearch(keyword, nextTags);
  }

  function clearAll() {
    setSelectedTags({});
    setKeyword("");
    setClips([]);
    setTotal(0);
    setSearched(false);
  }

  const hasFilters =
    keyword.trim().length > 0 || Object.keys(selectedTags).length > 0;

  return (
    <div className="space-y-4">
      {/* 搜索栏 */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索转录文本、话题、摘要..."
            className="pl-9"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") doSearch(keyword, selectedTags);
            }}
          />
        </div>
        <Button onClick={() => doSearch(keyword, selectedTags)} disabled={isPending}>
          {isPending ? "搜索中..." : "搜索"}
        </Button>
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearAll}>
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* 标签维度筛选面板 */}
      <div className="space-y-2">
        {Object.entries(allTags).map(([dimension, values]) => {
          const dim = dimension as TagDimension;
          return (
            <div key={dimension} className="flex flex-wrap items-center gap-1.5">
              <span className="text-xs font-medium text-muted-foreground w-12 shrink-0">
                {TAG_DIMENSION_LABELS[dim] || dimension}
              </span>
              {values.slice(0, 15).map((value) => {
                const isActive = selectedTags[dimension]?.has(value);
                return (
                  <Badge
                    key={`${dimension}-${value}`}
                    variant="outline"
                    className={`cursor-pointer text-xs transition-colors ${
                      isActive
                        ? TAG_DIMENSION_COLORS[dim] || "bg-primary text-primary-foreground"
                        : "hover:bg-muted"
                    }`}
                    onClick={() => toggleTag(dimension, value)}
                  >
                    {value}
                  </Badge>
                );
              })}
              {values.length > 15 && (
                <span className="text-xs text-muted-foreground">+{values.length - 15}</span>
              )}
            </div>
          );
        })}
      </div>

      {/* 结果统计 */}
      {searched && (
        <p className="text-xs text-muted-foreground">
          找到 {total} 个切片
          {total > 40 && " (显示前 40 个)"}
        </p>
      )}

      {/* 结果网格 */}
      {clips.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {clips.map((clip) => (
            <GlobalClipCard key={clip.id} clip={clip} />
          ))}
        </div>
      ) : searched ? (
        <div className="flex flex-col items-center py-12 text-muted-foreground">
          <Search className="h-10 w-10 opacity-30 mb-2" />
          <p className="text-sm">没有找到匹配的切片</p>
        </div>
      ) : (
        <div className="flex flex-col items-center py-12 text-muted-foreground">
          <Film className="h-10 w-10 opacity-30 mb-2" />
          <p className="text-sm">选择标签或输入关键词开始搜索</p>
        </div>
      )}
    </div>
  );
}

function GlobalClipCard({ clip }: { clip: ClipResult }) {
  const [showVideo, setShowVideo] = useState(false);
  const thumbUrl = `/api/projects/${clip.projectId}/clips/${clip.index}/thumbnail`;
  const videoUrl = `/api/projects/${clip.projectId}/clips/${clip.index}/video`;

  return (
    <Card className="overflow-hidden">
      <div className="relative aspect-video bg-muted">
        {showVideo ? (
          <video
            src={videoUrl}
            controls
            autoPlay
            className="h-full w-full object-contain"
            onEnded={() => setShowVideo(false)}
          />
        ) : (
          <>
            <img
              src={thumbUrl}
              alt={clip.topic || `Clip ${clip.index}`}
              width={640}
              height={360}
              className="h-full w-full object-cover"
            />
            <button
              onClick={() => setShowVideo(true)}
              aria-label="播放视频"
              className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 transition-opacity hover:opacity-100"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/90">
                <Play className="h-5 w-5 text-black" />
              </div>
            </button>
            <span className="absolute bottom-1 right-1 rounded bg-black/70 px-1.5 py-0.5 text-xs text-white">
              {formatTime(clip.duration)}
            </span>
          </>
        )}
      </div>

      <CardContent className="p-3 space-y-2">
        {/* 来源项目 */}
        <Link
          href={`/projects/${clip.projectId}`}
          className="text-[10px] text-primary hover:underline truncate block"
        >
          {clip.projectName}
        </Link>

        {/* 时间 + 话题 */}
        <div>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            {formatTime(clip.start)} - {formatTime(clip.end)}
          </div>
          {clip.topic && (
            <p className="mt-1 text-sm font-medium leading-tight line-clamp-2">
              {clip.topic}
            </p>
          )}
        </div>

        {/* 标签 */}
        <div className="flex flex-wrap gap-1">
          {clip.tags.slice(0, 5).map((tag, i) => {
            const dim = tag.dimension as TagDimension;
            return (
              <Badge
                key={i}
                variant="outline"
                className={`text-[10px] ${TAG_DIMENSION_COLORS[dim] || ""}`}
              >
                {tag.value}
              </Badge>
            );
          })}
        </div>

        {/* 操作 */}
        <div className="flex gap-1.5 pt-1">
          <Button
            variant="outline"
            size="sm"
            className="h-7 flex-1 text-xs"
            onClick={() => setShowVideo(true)}
          >
            <Play className="mr-1 h-3 w-3" />
            播放
          </Button>
          <a href={videoUrl} download>
            <Button variant="outline" size="sm" className="h-7 text-xs">
              <Download className="h-3 w-3" />
            </Button>
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
