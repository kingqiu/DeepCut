-- CreateEnum
CREATE TYPE "SourceType" AS ENUM ('upload', 'url', 'local_watch');

-- CreateEnum
CREATE TYPE "ProjectStatus" AS ENUM ('pending', 'processing', 'completed', 'failed');

-- CreateTable
CREATE TABLE "Project" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "source" "SourceType" NOT NULL,
    "sourcePath" TEXT NOT NULL,
    "status" "ProjectStatus" NOT NULL DEFAULT 'pending',
    "error" TEXT,
    "videoMeta" JSONB,
    "versionDir" TEXT,
    "totalClips" INTEGER NOT NULL DEFAULT 0,
    "elapsed" DOUBLE PRECISION,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "watchDirId" TEXT,

    CONSTRAINT "Project_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Clip" (
    "id" TEXT NOT NULL,
    "projectId" TEXT NOT NULL,
    "index" INTEGER NOT NULL,
    "start" DOUBLE PRECISION NOT NULL,
    "end" DOUBLE PRECISION NOT NULL,
    "duration" DOUBLE PRECISION NOT NULL,
    "fileName" TEXT NOT NULL,
    "filePath" TEXT NOT NULL,
    "thumbnailPath" TEXT NOT NULL,
    "splitReason" TEXT NOT NULL,
    "sceneGroup" INTEGER NOT NULL DEFAULT 0,
    "orientation" TEXT NOT NULL DEFAULT 'landscape',
    "transcriptText" TEXT NOT NULL DEFAULT '',
    "topic" TEXT NOT NULL DEFAULT '',
    "summary" TEXT NOT NULL DEFAULT '',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Clip_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ClipTag" (
    "id" TEXT NOT NULL,
    "clipId" TEXT NOT NULL,
    "dimension" TEXT NOT NULL,
    "value" TEXT NOT NULL,

    CONSTRAINT "ClipTag_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ClipRelationship" (
    "id" TEXT NOT NULL,
    "clipId" TEXT NOT NULL,
    "relatedClipIndex" INTEGER NOT NULL,
    "relationshipType" TEXT NOT NULL,

    CONSTRAINT "ClipRelationship_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "WatchDir" (
    "id" TEXT NOT NULL,
    "path" TEXT NOT NULL,
    "enabled" BOOLEAN NOT NULL DEFAULT true,
    "interval" INTEGER NOT NULL DEFAULT 600,
    "processedFiles" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "lastScan" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "WatchDir_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "Project_status_idx" ON "Project"("status");

-- CreateIndex
CREATE INDEX "Project_createdAt_idx" ON "Project"("createdAt");

-- CreateIndex
CREATE INDEX "Clip_projectId_idx" ON "Clip"("projectId");

-- CreateIndex
CREATE INDEX "Clip_topic_idx" ON "Clip"("topic");

-- CreateIndex
CREATE INDEX "ClipTag_dimension_value_idx" ON "ClipTag"("dimension", "value");

-- CreateIndex
CREATE INDEX "ClipTag_clipId_idx" ON "ClipTag"("clipId");

-- CreateIndex
CREATE INDEX "ClipRelationship_clipId_idx" ON "ClipRelationship"("clipId");

-- CreateIndex
CREATE UNIQUE INDEX "WatchDir_path_key" ON "WatchDir"("path");

-- AddForeignKey
ALTER TABLE "Project" ADD CONSTRAINT "Project_watchDirId_fkey" FOREIGN KEY ("watchDirId") REFERENCES "WatchDir"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Clip" ADD CONSTRAINT "Clip_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ClipTag" ADD CONSTRAINT "ClipTag_clipId_fkey" FOREIGN KEY ("clipId") REFERENCES "Clip"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ClipRelationship" ADD CONSTRAINT "ClipRelationship_clipId_fkey" FOREIGN KEY ("clipId") REFERENCES "Clip"("id") ON DELETE CASCADE ON UPDATE CASCADE;
