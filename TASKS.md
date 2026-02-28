# DeepCut - 任务清单

> 最后更新：2026-02-28 | 版本：v0.3（阶段一~三 MVP 完成）

## 阶段一：Python 切片引擎初始化 ★ MVP

| # | 任务 | 优先级 | 状态 |
|---|------|--------|------|
| 1.1 | 创建 `engine/` 目录，初始化 Python 项目 (`pyproject.toml`，uv) | 🔴 高 | ✅ 完成 |
| 1.2 | 安装核心依赖：scenedetect, opencv-python, faster-whisper, torch, openai, pydantic, typer, loguru | 🔴 高 | ✅ 完成 |
| 1.3 | 创建 `engine/.env.example`，定义所有环境变量 | 🔴 高 | ✅ 完成 |
| 1.4 | 实现全局配置 (`deepcut/config.py`)：Pydantic Settings，读取环境变量 | 🔴 高 | ✅ 完成 |
| 1.5 | 定义 Pydantic 数据模型 (`deepcut/models/`)：VideoInfo, VADResult, SceneChange, MotionChange, ClipPlan, ClipTags, OutputMetadata | 🔴 高 | ✅ 完成 |
| 1.6 | 实现日志配置 (`deepcut/utils/logging.py`)：loguru，终端进度输出 | 🟡 中 | ✅ 完成 |
| 1.7 | 实现版本目录生成 (`deepcut/utils/version.py`)：每次切片独立版本目录 | 🟡 中 | ✅ 完成 |
| 1.8 | 配置 `.gitignore`（Python + 视频文件 + 模型文件） | 🟡 中 | ✅ 完成 |
| 1.9 | 验证系统依赖：FFmpeg 8.0.1 ✅、Python 3.11.14 (uv) ✅、CLI 可运行 ✅、26 tests passed ✅ | 🟡 中 | ✅ 完成 |

---

## 阶段二：切片引擎核心模块

### 2A - 视频处理层 (`deepcut/video/`)

| # | 任务 | 优先级 | 状态 |
|---|------|--------|------|
| 2.1 | 实现视频探测 (`probe.py`)：FFmpeg 获取时长、分辨率、编码、画幅方向、fps | 🔴 高 | ✅ 完成 |
| 2.2 | 实现音频提取 (`extract.py`)：FFmpeg 提取 WAV 音频轨 + 视频切片提取 | 🔴 高 | ✅ 完成 |
| 2.3 | 实现视频切割 (`cutter.py`)：FFmpeg 关键帧对齐切割，输出 MP4 | 🔴 高 | ✅ 完成 |
| 2.4 | 实现工具函数 (`utils.py`)：时间格式转换、文件命名 | 🟡 中 | ✅ 完成 |
| 2.5 | 单元测试：用测试视频验证 probe、extract、cut 三个功能 | 🔴 高 | ✅ 完成 |

### 2B - 分析器 (`deepcut/analyzers/`)

| # | 任务 | 优先级 | 状态 |
|---|------|--------|------|
| 2.6 | 实现人声检测器 (`vad_detector.py`)：基于 faster-whisper 试探转录（替代 Silero VAD，鲁棒性更好） | 🔴 高 | ✅ 完成 |
| 2.7 | 实现场景检测器 (`scene_detector.py`)：PySceneDetect ContentDetector + ThresholdDetector | 🔴 高 | ✅ 完成 |
| 2.8 | 实现运镜检测器 (`motion_detector.py`)：OpenCV 稠密光流，识别平移/推拉/固定/突变 | 🔴 高 | ✅ 完成 |
| 2.9 | 实现语音转录器 (`transcriber.py`)：faster-whisper，带时间戳转录，支持中英混合 | 🔴 高 | ✅ 完成 |
| 2.10 | 单元测试：用三个测试视频分别验证 VAD、场景、运镜、转录 | 🔴 高 | ✅ 完成 |

### 2C - AI/LLM 服务 (`deepcut/ai/`)

| # | 任务 | 优先级 | 状态 |
|---|------|--------|------|
| 2.11 | 实现 LLM 客户端 (`llm_client.py`)：OpenAI/DashScope，指数退避重试，超时控制 | 🔴 高 | ✅ 完成 |
| 2.12 | 实现话题分段器 (`topic_segmenter.py`)：LLM 分析转录文本，输出话题变化点 | 🔴 高 | ✅ 完成 |
| 2.13 | 实现标签生成器 (`tag_generator.py`)：LLM 批量生成多维度标签 | 🔴 高 | ✅ 完成 |
| 2.14 | 编写 Prompt 模板：话题分段 + 标签生成 | 🔴 高 | ✅ 完成 |
| 2.15 | 单元测试：验证 LLM 调用、Prompt 效果 | 🟡 中 | ✅ 完成 |

### 2D - 融合决策引擎 (`deepcut/fusion/`)

| # | 任务 | 优先级 | 状态 |
|---|------|--------|------|
| 2.16 | 实现策略基类 + 工厂 (`strategy.py`)：根据 VAD 结果选择策略 | 🔴 高 | ✅ 完成 |
| 2.17 | 实现有人声策略 (SpeechFirstStrategy)：语义优先，场景+运镜辅助 | 🔴 高 | ✅ 完成 |
| 2.18 | 实现无人声策略 (VisualFirstStrategy)：场景优先，运镜辅助，固定间隔兜底 | 🔴 高 | ✅ 完成 |
| 2.19 | 实现融合引擎 (`engine.py`)：合并过短、拆分过长、添加重叠、场景组分配 | 🔴 高 | ✅ 完成 |
| 2.20 | 单元测试：用模拟数据验证融合逻辑和后处理（10 tests） | 🔴 高 | ✅ 完成 |

---

## 阶段三：Pipeline 集成与端到端测试

| # | 任务 | 优先级 | 状态 |
|---|------|--------|------|
| 3.1 | 实现 Step 1：视频预处理（probe + audio extract with loudnorm） | 🔴 高 | ✅ 完成 |
| 3.2 | 实现 Step 2：人声检测（Whisper 试探转录） | 🔴 高 | ✅ 完成 |
| 3.3 | 实现 Step 3A：有人声路径（Whisper 转录 + 场景 + 运镜） | 🔴 高 | ✅ 完成 |
| 3.4 | 实现 Step 3B：无人声路径（场景 + 运镜） | 🔴 高 | ✅ 完成 |
| 3.5 | 实现 Step 4：融合决策，输出 ClipPlan 列表 | 🔴 高 | ✅ 完成 |
| 3.6 | 实现 Step 5：FFmpeg 批量切割（stream copy） | 🔴 高 | ✅ 完成 |
| 3.7 | 实现 Step 6：AI 标签生成（需 OPENAI_API_KEY，无则跳过） | 🔴 高 | ✅ 完成 |
| 3.8 | 实现 Step 7：组装 metadata.json + transcript.json | 🔴 高 | ✅ 完成 |
| 3.9 | 实现 Pipeline Orchestrator (`orchestrator.py`)：编排 7 步、错误处理、计时、日志 | 🔴 高 | ✅ 完成 |
| 3.10 | 实现 CLI 入口 (`cli.py`)：typer，`deepcut slice` 命令 | 🔴 高 | ✅ 完成 |
| 3.11 | **端到端测试 A**：korean_restaurant.mp4（有人声 8.2min → 101 clips, 98.8s） | 🔴 高 | ✅ 完成 |
| 3.12 | **端到端测试 B**：silent_scenery.mp4（无人声 3.2min → 14 clips, 46.9s） | 🔴 高 | ✅ 完成 |
| 3.13 | **端到端测试 C**：test_video.mp4（实际无人声 9.9min → 视觉优先切片） | 🔴 高 | ✅ 完成 |
| 3.14 | 效果评估：人工检查切片质量，调优检测参数和融合策略 | 🔴 高 | 🔄 待人工评估 |

---

## 阶段四：Web 平台（MVP 后）

> **UI 参考原则**：参考 AutoClip 主操作模式（首页=输入+项目列表、详情页=切片展示），细节按 DeepCut 需求设计。详见 SPEC.md §8 和 ARCHITECTURE.md §4.2。

### 4A - Next.js 项目初始化

| # | 任务 | 优先级 | 状态 |
|---|------|--------|------|
| 4.1 | 创建 `web/` 目录，初始化 Next.js 14+ (TypeScript, App Router, Tailwind CSS 4) | 🟡 中 | ⬜ 待开始 |
| 4.2 | 安装 shadcn/ui、Zustand、Lucide React 等依赖 | 🟡 中 | ⬜ 待开始 |
| 4.3 | 配置 Prisma ORM，编写 schema.prisma (Video, ClipVersion, Clip, ClipTag, Transcript, ClipRelationship) | 🟡 中 | ⬜ 待开始 |
| 4.4 | 搭建 Docker Compose：PostgreSQL + Redis + Python Engine + Next.js | 🟡 中 | ⬜ 待开始 |

### 4B - Python Engine API 化

| # | 任务 | 优先级 | 状态 |
|---|------|--------|------|
| 4.5 | 实现 FastAPI 服务 (`engine/api/main.py`)：POST /api/slice, GET /api/status, GET /api/health | 🟡 中 | ⬜ 待开始 |
| 4.6 | 实现 Next.js 端 Python Engine HTTP 客户端 (`web/src/lib/engine-client/`) | 🟡 中 | ⬜ 待开始 |
| 4.7 | 实现 BullMQ 任务队列（Next.js 侧入队，触发 Python 引擎） | 🟡 中 | ⬜ 待开始 |

### 4C - 视频输入（参考 AutoClip 首页输入区模式）

| # | 任务 | 优先级 | 状态 |
|---|------|--------|------|
| 4.8 | 实现首页视频输入区：Tab 切换（文件上传 / 链接导入），参考 AutoClip HomePage 布局 | 🟡 中 | ⬜ 待开始 |
| 4.9 | 实现 VideoUploader 组件：拖拽上传 + 分片传输 + 进度条（不需要 SRT 上传） | 🟡 中 | ⬜ 待开始 |
| 4.10 | 实现 LinkImporter 组件：YouTube/B站 URL 粘贴 → 解析 → yt-dlp 下载（无视频分类选择） | 🟡 中 | ⬜ 待开始 |

### 4D - 管理界面（参考 AutoClip 项目列表 + 详情页模式）

| # | 任务 | 优先级 | 状态 |
|---|------|--------|------|
| 4.11 | 实现首页项目卡片网格列表 + 状态筛选（参考 AutoClip ProjectCard），增加画幅方向标记 | 🟡 中 | ⬜ 待开始 |
| 4.12 | 实现 TaskProgress 组件：SSE 实时进度推送（参考 AutoClip 进度条模式） | 🟡 中 | ⬜ 待开始 |
| 4.13 | 实现视频详情页：切片卡片网格（参考 AutoClip ClipCard），增加多维度标签展示 | 🟡 中 | ⬜ 待开始 |
| 4.14 | 实现 ClipCard 组件：缩略图 + 标题 + 摘要 + 标签 + 操作（播放/下载） | 🟡 中 | ⬜ 待开始 |
| 4.15 | 实现缩略图生成（FFmpeg 抽取代表帧） | 🟡 中 | ⬜ 待开始 |
| 4.16 | 实现全局片段库页面（🆕）：跨视频搜索、多维度标签筛选、画幅方向过滤 | 🟡 中 | ⬜ 待开始 |
| 4.17 | 实现下载功能：单片下载 + ZIP 批量下载 | 🟡 中 | ⬜ 待开始 |

---

## 阶段五：AI 重组引擎（远期）

| # | 任务 | 优先级 | 状态 |
|---|------|--------|------|
| 5.1 | 设计重组引擎架构：选片 + 排序 + 拼接 + 后处理 pipeline | 🟢 低 | ⬜ 待开始 |
| 5.2 | 实现 AI 选片：基于主题/标签从全局片段库匹配 | 🟢 低 | ⬜ 待开始 |
| 5.3 | 实现智能排序：AI 决定叙事顺序 | 🟢 低 | ⬜ 待开始 |
| 5.4 | 实现视频拼接 + 转场效果 | 🟢 低 | ⬜ 待开始 |
| 5.5 | 实现横屏→竖屏转换（智能裁切/主体居中/模糊填充） | � 低 | ⬜ 待开始 |
| 5.6 | 实现自动字幕生成 | � 低 | ⬜ 待开始 |
| 5.7 | 实现自动配乐 + 片头片尾 | 🟢 低 | ⬜ 待开始 |
| 5.8 | 实现批量输出（一次生成多个短视频） | � 低 | ⬜ 待开始 |

---

## 里程碑

| 里程碑 | 包含任务 | 目标 | 成功标准 |
|--------|----------|------|----------|
| **M1 - 引擎骨架** ✅ | 阶段一 (1.1-1.9) | Python 项目就绪，依赖安装完成 | 能运行空 CLI 命令 |
| **M2 - 模块可用** ✅ | 阶段二 (2.1-2.20) | 所有分析器和融合引擎单独可用 | 57 个单元测试通过 |
| **M3 - MVP 交付 ★** ✅ | 阶段三 (3.1-3.14) | 完整 pipeline 端到端可用 | 三个测试视频切片完成，待人工评估 |
| **M4 - Web 平台** | 阶段四 (4.1-4.17) | Web 管理界面上线 | 用户可上传/预览/下载/片段库浏览 |
| **M5 - AI 重组** | 阶段五 (5.1-5.8) | 自动重组引擎可用 | 给主题生成可发布短视频 |
