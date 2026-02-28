import { Queue } from "bullmq";
import { redisConnection } from "./connection";

export const processQueue = new Queue("deepcut-process", {
  connection: redisConnection,
  defaultJobOptions: {
    attempts: 1,
    removeOnComplete: { count: 100 },
    removeOnFail: { count: 50 },
  },
});

export interface ProcessJobData {
  projectId: string;
  videoPath: string;
  outputDir?: string;
  minDuration?: number;
  maxDuration?: number;
  disableMotion?: boolean;
  disableSpeech?: boolean;
}
