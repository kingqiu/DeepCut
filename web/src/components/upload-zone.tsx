"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Upload, Film, FolderOpen, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";

export function UploadZone() {
  const router = useRouter();
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [localPath, setLocalPath] = useState("");
  const [submittingPath, setSubmittingPath] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) await uploadFile(file);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) await uploadFile(file);
      e.target.value = "";
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  async function uploadFile(file: File) {
    if (!file.name.match(/\.(mp4|mkv|avi|mov|flv|wmv|webm)$/i)) {
      setMessage({ type: "error", text: "不支持的视频格式" });
      return;
    }
    if (file.size > 500 * 1024 * 1024) {
      setMessage({ type: "error", text: "文件超过 500MB 限制" });
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setMessage(null);

    try {
      // 模拟上传进度（fetch 不支持 upload progress, 用定时器模拟）
      const progressTimer = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 8, 90));
      }, 200);

      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/upload", { method: "POST", body: formData });
      clearInterval(progressTimer);
      setUploadProgress(100);

      const data = await res.json();

      if (!res.ok) {
        setMessage({ type: "error", text: data.error || "上传失败" });
      } else {
        setMessage({ type: "success", text: `${file.name} 已提交处理，正在切片中...` });
        // 刷新 Server Component 数据让项目卡片出现
        router.refresh();
      }
    } catch {
      setMessage({ type: "error", text: "网络错误" });
    } finally {
      setUploading(false);
      setTimeout(() => setUploadProgress(0), 500);
    }
  }

  async function handleLocalPathSubmit() {
    if (!localPath.trim()) return;
    setSubmittingPath(true);
    setMessage(null);

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ videoPath: localPath.trim() }),
      });
      const data = await res.json();

      if (!res.ok) {
        setMessage({ type: "error", text: data.error || "提交失败" });
      } else {
        setMessage({ type: "success", text: `${localPath.split("/").pop()} 已提交处理，正在切片中...` });
        setLocalPath("");
        router.refresh();
      }
    } catch {
      setMessage({ type: "error", text: "网络错误" });
    } finally {
      setSubmittingPath(false);
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <Tabs defaultValue="upload">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="upload" className="gap-2">
              <Upload className="h-4 w-4" />
              文件上传
            </TabsTrigger>
            <TabsTrigger value="local" className="gap-2">
              <FolderOpen className="h-4 w-4" />
              本地路径
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="mt-4">
            <div
              className={`relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
                isDragging
                  ? "border-primary bg-primary/5"
                  : "border-muted-foreground/25 hover:border-primary/50"
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {uploading ? (
                <div className="flex flex-col items-center w-full max-w-xs">
                  <Loader2 className="h-10 w-10 animate-spin text-primary" />
                  <p className="mt-3 text-sm text-muted-foreground">上传中...</p>
                  <Progress value={uploadProgress} className="mt-3 w-full" />
                  <p className="mt-1 text-xs text-muted-foreground/60">{uploadProgress}%</p>
                </div>
              ) : (
                <>
                  <Film className="h-10 w-10 text-muted-foreground" />
                  <p className="mt-3 text-sm text-muted-foreground">
                    拖拽视频文件到这里，或点击选择
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground/60">
                    支持 MP4/MKV/AVI/MOV，最大 500MB
                  </p>
                  <label className="mt-4 cursor-pointer">
                    <Button variant="outline" size="sm" asChild>
                      <span>选择文件</span>
                    </Button>
                    <input
                      type="file"
                      className="hidden"
                      accept="video/*"
                      onChange={handleFileSelect}
                    />
                  </label>
                </>
              )}
            </div>
          </TabsContent>

          <TabsContent value="local" className="mt-4">
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                输入服务器上的视频文件绝对路径
              </p>
              <div className="flex gap-2">
                <Input
                  placeholder="/path/to/video.mp4"
                  value={localPath}
                  onChange={(e) => setLocalPath(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleLocalPathSubmit()}
                  disabled={submittingPath}
                />
                <Button
                  onClick={handleLocalPathSubmit}
                  disabled={!localPath.trim() || submittingPath}
                >
                  {submittingPath ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    "提交"
                  )}
                </Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {message && (
          <div
            className={`mt-4 rounded-md px-3 py-2 text-sm ${
              message.type === "success"
                ? "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300"
                : "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
            }`}
          >
            {message.text}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
