"use client";

import { ReactNode } from "react";
import { FolderOpen, Search } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface HomeTabsProps {
  projectsTab: ReactNode;
  clipsTab: ReactNode;
}

export function HomeTabs({ projectsTab, clipsTab }: HomeTabsProps) {
  return (
    <Tabs defaultValue="projects">
      <TabsList>
        <TabsTrigger value="projects" className="gap-1.5">
          <FolderOpen className="h-4 w-4" />
          按项目
        </TabsTrigger>
        <TabsTrigger value="clips" className="gap-1.5">
          <Search className="h-4 w-4" />
          全局片段库
        </TabsTrigger>
      </TabsList>

      <TabsContent value="projects" className="mt-4">
        {projectsTab}
      </TabsContent>

      <TabsContent value="clips" className="mt-4">
        {clipsTab}
      </TabsContent>
    </Tabs>
  );
}
