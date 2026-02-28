"use client";

import { useState, useMemo } from "react";
import { Download, Play, Clock, Tag } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  TAG_DIMENSION_COLORS,
  TAG_DIMENSION_LABELS,
  type TagDimension,
} from "@/types";

interface ClipData {
  id: string;
  index: number;
  start: number;
  end: number;
  duration: number;
  fileName: string;
  thumbnailPath: string;
  splitReason: string;
  orientation: string;
  transcriptText: string;
  topic: string;
  summary: string;
  tags: Array<{ id: string; dimension: string; value: string }>;
  relationships: Array<{
    id: string;
    relatedClipIndex: number;
    relationshipType: string;
  }>;
}

interface ClipGridProps {
  projectId: string;
  clips: ClipData[];
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function ClipGrid({ projectId, clips }: ClipGridProps) {
  const [selectedDimension, setSelectedDimension] = useState<string | null>(null);
  const [selectedValues, setSelectedValues] = useState<Set<string>>(new Set());

  // 收集所有标签维度和值
  const tagMap = useMemo(() => {
    const map: Record<string, Set<string>> = {};
    for (const clip of clips) {
      for (const tag of clip.tags) {
        if (!map[tag.dimension]) map[tag.dimension] = new Set();
        map[tag.dimension].add(tag.value);
      }
    }
    return map;
  }, [clips]);

  // 筛选切片
  const filteredClips = useMemo(() => {
    if (!selectedDimension || selectedValues.size === 0) return clips;
    return clips.filter((clip) =>
      clip.tags.some(
        (t) => t.dimension === selectedDimension && selectedValues.has(t.value)
      )
    );
  }, [clips, selectedDimension, selectedValues]);

  function toggleTag(dimension: string, value: string) {
    if (selectedDimension !== dimension) {
      setSelectedDimension(dimension);
      setSelectedValues(new Set([value]));
    } else {
      const next = new Set(selectedValues);
      if (next.has(value)) {
        next.delete(value);
        if (next.size === 0) setSelectedDimension(null);
      } else {
        next.add(value);
      }
      setSelectedValues(next);
    }
  }

  function clearFilter() {
    setSelectedDimension(null);
    setSelectedValues(new Set());
  }

  return (
    <div className="space-y-4">
      {/* 标签筛选栏 */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Tag className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">标签筛选</span>
          {selectedDimension && (
            <Button variant="ghost" size="sm" onClick={clearFilter} className="h-6 text-xs">
              清除
            </Button>
          )}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(tagMap).map(([dimension, values]) => (
            <div key={dimension} className="flex flex-wrap gap-1">
              {Array.from(values)
                .slice(0, 8)
                .map((value) => {
                  const isActive =
                    selectedDimension === dimension && selectedValues.has(value);
                  const dim = dimension as TagDimension;
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
                      <span className="mr-1 opacity-60">
                        {TAG_DIMENSION_LABELS[dim] || dimension}
                      </span>
                      {value}
                    </Badge>
                  );
                })}
            </div>
          ))}
        </div>
      </div>

      {/* 切片数统计 */}
      <p className="text-xs text-muted-foreground">
        共 {filteredClips.length} 个切片
        {selectedDimension && ` (筛选自 ${clips.length} 个)`}
      </p>

      {/* 切片网格 */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filteredClips.map((clip) => (
          <ClipCard key={clip.id} projectId={projectId} clip={clip} />
        ))}
      </div>
    </div>
  );
}

function ClipCard({ projectId, clip }: { projectId: string; clip: ClipData }) {
  const [showVideo, setShowVideo] = useState(false);
  const thumbUrl = `/api/projects/${projectId}/clips/${clip.index}/thumbnail`;
  const videoUrl = `/api/projects/${projectId}/clips/${clip.index}/video`;

  return (
    <Card className="overflow-hidden">
      {/* 视频/缩略图区域 */}
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
              alt={`Clip ${clip.index}`}
              className="h-full w-full object-cover"
            />
            <button
              onClick={() => setShowVideo(true)}
              className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 transition-opacity hover:opacity-100"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/90">
                <Play className="h-5 w-5 text-black" />
              </div>
            </button>
            {/* 时长角标 */}
            <span className="absolute bottom-1 right-1 rounded bg-black/70 px-1.5 py-0.5 text-xs text-white">
              {formatTime(clip.duration)}
            </span>
          </>
        )}
      </div>

      <CardContent className="p-3 space-y-2">
        {/* 时间范围 + 话题 */}
        <div>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            {formatTime(clip.start)} - {formatTime(clip.end)}
            <span className="ml-auto text-xs opacity-60">#{clip.index}</span>
          </div>
          {clip.topic && (
            <p className="mt-1 text-sm font-medium leading-tight line-clamp-2">
              {clip.topic}
            </p>
          )}
        </div>

        {/* 标签 */}
        <div className="flex flex-wrap gap-1">
          {clip.tags.slice(0, 6).map((tag) => {
            const dim = tag.dimension as TagDimension;
            return (
              <Badge
                key={tag.id}
                variant="outline"
                className={`text-[10px] ${TAG_DIMENSION_COLORS[dim] || ""}`}
              >
                {tag.value}
              </Badge>
            );
          })}
          {clip.tags.length > 6 && (
            <Badge variant="outline" className="text-[10px]">
              +{clip.tags.length - 6}
            </Badge>
          )}
        </div>

        {/* 操作按钮 */}
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
