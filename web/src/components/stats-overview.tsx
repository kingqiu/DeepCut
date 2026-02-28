"use client";

import { useEffect, useState } from "react";

interface StatsData {
  totalProjects: number;
  processing: number;
  completed: number;
  totalClips: number;
}

// 生成确定性的柱状图数据（避免 Hydration 错误）
function generateBars(count: number, value: number, seed: number) {
  const bars = [];
  for (let i = 0; i < count; i++) {
    // 使用确定性算法生成高度，避免 Math.random()
    const baseHeight = value > 0 ? 20 : 10;
    // 使用正弦波生成变化，基于索引和种子
    const wave = Math.sin((i + seed) * 0.5) * 15 + 15;
    const trendBoost = i > count - 3 ? 15 : 0;
    bars.push(baseHeight + wave + trendBoost);
  }
  return bars;
}

export function StatsOverview() {
  const [stats, setStats] = useState<StatsData>({
    totalProjects: 0,
    processing: 0,
    completed: 0,
    totalClips: 0,
  });

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await fetch("/api/stats");
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      }
    }
    fetchStats();
  }, []);

  const statCards = [
    {
      label: "总项目",
      value: stats.totalProjects,
      bars: generateBars(15, stats.totalProjects, 0),
    },
    {
      label: "处理中",
      value: stats.processing,
      bars: generateBars(15, stats.processing, 1),
    },
    {
      label: "已完成",
      value: stats.completed,
      bars: generateBars(15, stats.completed, 2),
    },
    {
      label: "切片总数",
      value: stats.totalClips,
      bars: generateBars(15, stats.totalClips, 3),
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {statCards.map((stat, index) => (
        <div
          key={index}
          className="group relative overflow-hidden rounded-xl bg-gradient-to-br from-background to-muted/30 p-6 transition-all hover:shadow-lg hover:-translate-y-1"
        >
          {/* 标签 */}
          <div className="mb-2">
            <span className="text-xs font-medium text-muted-foreground">
              {stat.label}
            </span>
          </div>

          {/* 大数字 */}
          <div className="mb-4 text-4xl font-bold text-primary">
            {stat.value}
          </div>

          {/* 柱状图 */}
          <div className="flex items-end gap-0.5 h-16">
            {stat.bars.map((height, i) => (
              <div
                key={i}
                className="flex-1 rounded-t-sm bg-primary/80 transition-all group-hover:bg-primary"
                style={{
                  height: `${height.toFixed(2)}%`,
                  opacity: stat.value === 0 ? 0.2 : 0.8,
                }}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
