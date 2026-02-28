/** 项目来源类型 */
export const SOURCE_TYPES = {
  upload: "upload",
  url: "url",
  local_watch: "local_watch",
} as const;

export type SourceType = (typeof SOURCE_TYPES)[keyof typeof SOURCE_TYPES];

/** 项目状态 */
export const PROJECT_STATUSES = {
  pending: "pending",
  processing: "processing",
  completed: "completed",
  failed: "failed",
} as const;

export type ProjectStatus =
  (typeof PROJECT_STATUSES)[keyof typeof PROJECT_STATUSES];

/** 标签维度 */
export const TAG_DIMENSIONS = {
  content: "content",
  scene: "scene",
  object: "object",
  action: "action",
  emotion: "emotion",
  technical: "technical",
  purpose: "purpose",
} as const;

export type TagDimension =
  (typeof TAG_DIMENSIONS)[keyof typeof TAG_DIMENSIONS];

/** 标签维度中文映射 */
export const TAG_DIMENSION_LABELS: Record<TagDimension, string> = {
  content: "内容",
  scene: "场景",
  object: "物体",
  action: "动作",
  emotion: "情感",
  technical: "技术",
  purpose: "用途",
};

/** 标签维度颜色 */
export const TAG_DIMENSION_COLORS: Record<TagDimension, string> = {
  content: "bg-blue-100 text-blue-800",
  scene: "bg-green-100 text-green-800",
  object: "bg-yellow-100 text-yellow-800",
  action: "bg-red-100 text-red-800",
  emotion: "bg-purple-100 text-purple-800",
  technical: "bg-gray-100 text-gray-800",
  purpose: "bg-orange-100 text-orange-800",
};

/** 项目状态中文映射 */
export const PROJECT_STATUS_LABELS: Record<ProjectStatus, string> = {
  pending: "等待处理",
  processing: "处理中",
  completed: "已完成",
  failed: "失败",
};
