import { join } from "path";
import { homedir } from "os";

export const STORAGE_ROOT =
  process.env.DEEPCUT_STORAGE_ROOT ?? join(homedir(), "deepcut-data");

export const UPLOADS_DIR = join(STORAGE_ROOT, "uploads");
export const OUTPUT_DIR = join(STORAGE_ROOT, "output");
export const CACHE_DIR = join(STORAGE_ROOT, "cache");

export function getProjectUploadDir(projectId: string): string {
  return join(UPLOADS_DIR, projectId);
}

export function getProjectOutputDir(projectId: string): string {
  return join(OUTPUT_DIR, projectId);
}
