/** Shared Redis connection config for BullMQ (avoids ioredis version mismatch) */

const redisUrl = new URL(process.env.REDIS_URL ?? "redis://localhost:6379");

export const redisConnection = {
  host: redisUrl.hostname,
  port: Number(redisUrl.port || 6379),
};
