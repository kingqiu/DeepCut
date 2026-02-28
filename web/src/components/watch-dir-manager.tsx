"use client";

import { useState, useEffect, useCallback } from "react";
import { Plus, Trash2, FolderOpen, Loader2, ToggleLeft, ToggleRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

interface WatchDir {
  id: string;
  path: string;
  enabled: boolean;
  interval: number;
  lastScan: string | null;
  createdAt: string;
  _count: { projects: number };
}

export function WatchDirManager() {
  const [dirs, setDirs] = useState<WatchDir[]>([]);
  const [loading, setLoading] = useState(true);
  const [newPath, setNewPath] = useState("");
  const [newInterval, setNewInterval] = useState(600);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDirs = useCallback(async () => {
    const res = await fetch("/api/watch-dirs");
    if (res.ok) setDirs(await res.json());
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchDirs();
  }, [fetchDirs]);

  async function handleAdd() {
    if (!newPath.trim()) return;
    setAdding(true);
    setError(null);

    const res = await fetch("/api/watch-dirs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: newPath.trim(), interval: newInterval }),
    });

    if (res.ok) {
      setNewPath("");
      setNewInterval(600);
      await fetchDirs();
    } else {
      const data = await res.json();
      setError(data.error || "添加失败");
    }
    setAdding(false);
  }

  async function handleToggle(id: string, enabled: boolean) {
    await fetch(`/api/watch-dirs/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !enabled }),
    });
    await fetchDirs();
  }

  async function handleUpdateInterval(id: string, interval: number) {
    await fetch(`/api/watch-dirs/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ interval }),
    });
    await fetchDirs();
  }

  async function handleDelete(id: string) {
    if (!confirm("确定删除此监听目录？")) return;
    await fetch(`/api/watch-dirs/${id}`, { method: "DELETE" });
    await fetchDirs();
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 添加新目录 */}
      <Card>
        <CardContent className="pt-4 space-y-3">
          <div className="flex gap-2">
            <Input
              name="watchPath"
              autoComplete="off"
              placeholder="/path/to/video/directory"
              value={newPath}
              onChange={(e) => setNewPath(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAdd()}
              disabled={adding}
            />
            <div className="flex items-center gap-1.5 shrink-0">
              <Input
                type="number"
                name="scanInterval"
                aria-label="扫描间隔（秒）"
                className="w-24"
                value={newInterval}
                onChange={(e) => setNewInterval(Number(e.target.value))}
                min={60}
                step={60}
                disabled={adding}
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">秒</span>
            </div>
            <Button onClick={handleAdd} disabled={!newPath.trim() || adding} className="shrink-0">
              {adding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            </Button>
          </div>
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </CardContent>
      </Card>

      {/* 目录列表 */}
      {dirs.length === 0 ? (
        <div className="flex flex-col items-center py-8 text-muted-foreground">
          <FolderOpen className="h-10 w-10 opacity-30 mb-2" />
          <p className="text-sm">暂未配置监听目录</p>
        </div>
      ) : (
        <div className="space-y-2">
          {dirs.map((dir) => (
            <Card key={dir.id}>
              <CardContent className="flex items-center gap-3 py-3">
                <button
                  onClick={() => handleToggle(dir.id, dir.enabled)}
                  onKeyDown={(e) => e.key === 'Enter' && handleToggle(dir.id, dir.enabled)}
                  aria-label={dir.enabled ? "禁用监听" : "启用监听"}
                  className="shrink-0"
                >
                  {dir.enabled ? (
                    <ToggleRight className="h-6 w-6 text-primary" />
                  ) : (
                    <ToggleLeft className="h-6 w-6 text-muted-foreground" />
                  )}
                </button>

                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">{dir.path}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <Badge variant="outline" className="text-[10px]">
                      {dir._count.projects} 个项目
                    </Badge>
                    <span className="text-[10px] text-muted-foreground">
                      间隔:
                    </span>
                    <select
                      className="text-[10px] border rounded px-1 py-0.5 bg-background text-foreground"
                      value={dir.interval}
                      onChange={(e) => handleUpdateInterval(dir.id, Number(e.target.value))}
                    >
                      <option value={60}>1 分钟</option>
                      <option value={300}>5 分钟</option>
                      <option value={600}>10 分钟</option>
                      <option value={1800}>30 分钟</option>
                      <option value={3600}>1 小时</option>
                    </select>
                    {dir.lastScan && (
                      <span className="text-[10px] text-muted-foreground">
                        上次扫描: {new Date(dir.lastScan).toLocaleTimeString("zh-CN")}
                      </span>
                    )}
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(dir.id)}
                  className="shrink-0 text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
