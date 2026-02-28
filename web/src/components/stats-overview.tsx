"use client";

import { useEffect, useState } from "react";
import { Film, Clock, CheckCircle2, Scissors } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface StatsData {
  totalProjects: number;
  processing: number;
  completed: number;
  totalClips: number;
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
      icon: Film,
      color: "text-primary",
      bgColor: "bg-primary/10",
    },
    {
      label: "处理中",
      value: stats.processing,
      icon: Clock,
      color: "text-chart-2",
      bgColor: "bg-chart-2/10",
    },
    {
      label: "已完成",
      value: stats.completed,
      icon: CheckCircle2,
      color: "text-green-600",
      bgColor: "bg-green-50",
    },
    {
      label: "切片总数",
      value: stats.totalClips,
      icon: Scissors,
      color: "text-primary",
      bgColor: "bg-primary/10",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {statCards.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <Card
            key={index}
            className="overflow-hidden transition-all hover:shadow-lg hover:-translate-y-1"
          >
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    {stat.label}
                  </p>
                  <p className="mt-2 text-3xl font-bold text-foreground">
                    {stat.value}
                  </p>
                </div>
                <div className={`rounded-full p-3 ${stat.bgColor}`}>
                  <Icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
              <div className="mt-4 h-1 w-full rounded-full bg-muted">
                <div
                  className={`h-full rounded-full ${stat.color.replace('text-', 'bg-')} transition-all`}
                  style={{
                    width: stat.value > 0 ? "100%" : "0%",
                  }}
                />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
