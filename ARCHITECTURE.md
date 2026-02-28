# DeepCut - 系统架构设计

> 最后更新：2026-02-28 | 版本：v0.2（需求沟通后重写）

## 1. 架构总览

DeepCut 采用 **Python + Next.js 混合架构**：
- **Python 切片引擎**：独立服务，负责视频分析、切片、标签生成等计算密集型任务
- **Next.js Web 层**（第二阶段）：负责用户界面、任务调度、数据管理

### 1.1 MVP 架构（切片引擎）

```
┌─────────────────────────────────────────────────────────────────┐
│                    Python 切片引擎 (CLI)                         │
│                                                                 │
│  deepcut-cli --input video.mp4 --duration-preference medium     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Pipeline Orchestrator                  │    │
│  │  管理 7 步流水线的执行顺序、错误处理、进度日志          │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐   │
│  │ Step 1: 预处理                                           │   │
│  │  FFmpeg probe → 提取音频 → 记录视频元信息                │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐   │
│  │ Step 2: VAD (人声活动检测)                                │   │
│  │  Silero VAD / Whisper → has_speech + 人声区间列表         │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                          │                                      │
│            ┌─────────────┴─────────────┐                       │
│            ▼                           ▼                        │
│  ┌──────────────────┐    ┌──────────────────────────┐          │
│  │ Step 3A: 有人声  │    │ Step 3B: 无人声          │          │
│  │ Whisper 转录     │    │ 纯视觉分析               │          │
│  │ + 场景检测       │    │ 场景 + 运镜              │          │
│  │ + 运镜检测       │    │                          │          │
│  └────────┬─────────┘    └────────────┬─────────────┘          │
│            │                           │                        │
│            └─────────────┬─────────────┘                       │
│                          ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Step 4: 融合决策                                          │  │
│  │  多维度切分点 → 合并/拆分 → 最终切片方案                   │  │
│  └──────────────────────┬──────────────────────────────────┘  │
│                          ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Step 5: FFmpeg 视频切割                                    │  │
│  └──────────────────────┬──────────────────────────────────┘  │
│                          ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Step 6: AI 标签生成 (LLM)                                 │  │
│  └──────────────────────┬──────────────────────────────────┘  │
│                          ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Step 7: 输出（视频文件 + metadata.json + transcript.json）│  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │  本地文件系统              │
            │  {video_dir}/deepcut_output/│
            │  └── v1_20260228_1430/    │
            │      ├── clips/*.mp4      │
            │      ├── metadata.json    │
            │      └── transcript.json  │
            └──────────────────────────┘
```

### 1.2 完整架构（第二阶段 Web 平台）

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端 (Browser)                         │
│  Next.js App (React + Tailwind + shadcn/ui)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ 上传页面 │ │ 视频列表 │ │ 切片预览 │ │ 实时进度 (SSE)   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────────┐
│                     Next.js 服务端                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  App Router      │  │  API Routes     │  │  Server Actions │  │
│  │  (页面渲染)      │  │  (REST API)     │  │  (数据变更)     │  │
│  └─────────────────┘  └────────┬────────┘  └───────┬────────┘  │
│                                │                    │           │
│  ┌─────────────────────────────▼────────────────────▼────────┐  │
│  │                    业务层                                  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │  │
│  │  │ storage/ │ │ queue/   │ │ db/      │ │ engine-      │ │  │
│  │  │ S3/本地  │ │ BullMQ   │ │ Prisma   │ │ client/      │ │  │
│  │  │          │ │ 任务入队 │ │          │ │ 调用Python   │ │  │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘ │  │
│  └───────┼─────────────┼────────────┼──────────────┼─────────┘  │
└──────────┼─────────────┼────────────┼──────────────┼────────────┘
           │             │            │              │
     ┌─────▼─────┐ ┌────▼────┐ ┌────▼─────┐  ┌────▼──────────────────┐
     │  文件存储  │ │  Redis  │ │PostgreSQL│  │  Python 切片引擎       │
     │  S3/本地  │ │         │ │ (Prisma) │  │  (FastAPI 服务)        │
     └───────────┘ └────┬────┘ └──────────┘  │  ┌──────────────────┐  │
                        │                     │  │ /api/slice       │  │
              ┌─────────▼──────────┐          │  │ /api/status      │  │
              │  BullMQ Workers    │          │  │ /api/health      │  │
              │  (Next.js 侧)     │          │  └──────────────────┘  │
              │  任务编排 + 状态管理│          │         │              │
              └────────┬───────────┘          │  ┌──────▼───────────┐  │
                       │ HTTP                 │  │ 切片 Pipeline     │  │
                       └──────────────────────►  │ (7 步流水线)     │  │
                                              │  └──────────────────┘  │
                                              └────────────────────────┘
```

**通信方式选型（Python ↔ Next.js）：**

| 方案 | 适用场景 | 选择 |
|------|----------|------|
| FastAPI HTTP 服务 | 实时调用 + 状态查询 | ✅ 主通信方式 |
| Redis 任务队列 | 长时间异步任务 | ✅ 辅助（Web 阶段） |
| CLI 子进程 | MVP 阶段直接使用 | ✅ MVP 入口 |

选择 FastAPI 作为主通信方式的原因：
- 性能好（uvicorn + async），适合处理并发请求
- 原生支持 WebSocket/SSE，可实时推送处理进度
- Python 生态天然支持所有视频/AI 依赖库
- 独立部署、独立扩展，不与 Next.js 耦合
- Web 阶段 Next.js 通过 HTTP 调用，解耦清晰

---

## 2. Python 切片引擎模块设计

### 2.1 项目结构

```
engine/                              # Python 切片引擎根目录
├── pyproject.toml                   # 项目配置 + 依赖管理 (Poetry/uv)
├── README.md
├── .env.example
│
├── deepcut/                         # 主包
│   ├── __init__.py
│   ├── cli.py                       # CLI 入口 (click/typer)
│   ├── config.py                    # 全局配置 (Pydantic Settings)
│   │
│   ├── pipeline/                    # 7 步流水线
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # 流水线编排器
│   │   ├── step1_preprocess.py      # 视频预处理
│   │   ├── step2_vad.py             # 人声活动检测
│   │   ├── step3a_speech_analysis.py # 有人声分析（Whisper + 场景 + 运镜）
│   │   ├── step3b_visual_analysis.py # 无人声分析（场景 + 运镜）
│   │   ├── step4_fusion.py          # 融合决策
│   │   ├── step5_cut.py             # 视频切割
│   │   ├── step6_tagging.py         # AI 标签生成
│   │   └── step7_output.py          # 输出组装
│   │
│   ├── analyzers/                   # 分析器（可独立使用的检测模块）
│   │   ├── __init__.py
│   │   ├── scene_detector.py        # PySceneDetect 封装
│   │   ├── motion_detector.py       # OpenCV 光流运镜检测
│   │   ├── vad_detector.py          # 人声活动检测 (Silero VAD)
│   │   └── transcriber.py           # Whisper 语音转录
│   │
│   ├── fusion/                      # 融合决策引擎
│   │   ├── __init__.py
│   │   ├── strategy.py              # 策略基类 + 工厂
│   │   ├── speech_priority.py       # 有人声策略（语义优先）
│   │   ├── visual_priority.py       # 无人声策略（视觉优先）
│   │   └── post_processor.py        # 通用后处理（合并/拆分/重叠）
│   │
│   ├── ai/                          # AI/LLM 服务封装
│   │   ├── __init__.py
│   │   ├── llm_client.py            # LLM 客户端 (OpenAI/DashScope)
│   │   ├── topic_segmenter.py       # LLM 话题分段
│   │   ├── tag_generator.py         # LLM 标签生成
│   │   └── prompts/                 # Prompt 模板
│   │       ├── topic_segmentation.py
│   │       └── tag_generation.py
│   │
│   ├── video/                       # FFmpeg 封装
│   │   ├── __init__.py
│   │   ├── probe.py                 # 视频信息探测
│   │   ├── audio_extract.py         # 音频提取
│   │   ├── cutter.py                # 视频切割
│   │   └── utils.py                 # 时间格式转换等
│   │
│   ├── models/                      # 数据模型 (Pydantic)
│   │   ├── __init__.py
│   │   ├── video.py                 # VideoInfo, VideoConfig
│   │   ├── clip.py                  # Clip, ClipPlan, ClipTag
│   │   ├── analysis.py              # SceneChange, MotionChange, VADResult
│   │   └── metadata.py              # OutputMetadata, TranscriptData
│   │
│   └── utils/                       # 工具函数
│       ├── __init__.py
│       ├── logging.py               # 日志配置
│       ├── timer.py                 # 计时器
│       └── version.py               # 版本目录生成
│
├── api/                             # FastAPI 服务（第二阶段）
│   ├── __init__.py
│   ├── main.py                      # FastAPI app
│   ├── routes/
│   │   ├── slice.py                 # POST /api/slice
│   │   ├── status.py                # GET /api/status/{task_id}
│   │   └── health.py                # GET /api/health
│   └── deps.py                      # 依赖注入
│
└── tests/
    ├── conftest.py
    ├── test_scene_detector.py
    ├── test_motion_detector.py
    ├── test_vad.py
    ├── test_fusion.py
    ├── test_pipeline.py
    └── fixtures/                    # 测试用的短视频片段
```

### 2.2 核心依赖

| 依赖 | 用途 | 说明 |
|------|------|------|
| **scenedetect** | 场景检测 | PySceneDetect，本地运行 |
| **opencv-python** | 运镜/光流检测 | OpenCV，本地运行 |
| **openai-whisper** / **faster-whisper** | 语音转录 | 本地模型或 API |
| **silero-vad** | 人声活动检测 | 轻量 VAD 模型，本地运行 |
| **openai** | LLM 调用 | GPT-4o 用于话题分段 + 标签生成 |
| **ffmpeg-python** / subprocess | 视频处理 | FFmpeg 封装 |
| **pydantic** | 数据模型 | 输入输出校验 |
| **click** / **typer** | CLI 框架 | 命令行参数解析 |
| **fastapi** + **uvicorn** | HTTP 服务 | 第二阶段 |
| **loguru** | 日志 | 结构化日志 |

### 2.3 Pipeline Orchestrator 设计

```python
class PipelineOrchestrator:
    """流水线编排器 - 管理 7 步执行"""

    def run(self, config: PipelineConfig) -> OutputMetadata:
        """
        主执行流程：
        1. preprocess(video_path) → VideoInfo
        2. detect_vad(audio_path) → VADResult
        3. if has_speech → speech_analysis() → AnalysisResult
           else        → visual_analysis() → AnalysisResult
        4. fusion(analysis, config) → List[ClipPlan]
        5. cut(video_path, clip_plans) → List[ClipFile]
        6. tag(clip_plans, transcript?) → List[ClipWithTags]
        7. output(clips, metadata) → OutputMetadata
        """
```

**关键设计决策：**

- 每一步都是独立函数，可单独测试和调试
- 步骤之间通过 Pydantic 模型传递数据，类型安全
- Orchestrator 负责错误处理、日志、计时
- 步骤 3A 中的三个分析器（Whisper、场景、运镜）**并行执行**（`asyncio.gather` 或 `concurrent.futures`）

### 2.4 分析器设计

#### SceneDetector（场景检测）

```python
class SceneDetector:
    """基于 PySceneDetect 的场景检测"""

    def detect(self, video_path: str) -> List[SceneChange]:
        """
        返回场景变化点列表：
        [
          SceneChange(timestamp=12.5, confidence=0.85, type="cut"),
          SceneChange(timestamp=45.2, confidence=0.72, type="dissolve"),
        ]
        """
```

使用 PySceneDetect 的 `ContentDetector`（基于帧间差异）+ `ThresholdDetector`（基于亮度变化）双检测器，取并集后去重。

#### MotionDetector（运镜变化检测）

```python
class MotionDetector:
    """基于 OpenCV 光流的运镜变化检测"""

    def detect(self, video_path: str) -> List[MotionChange]:
        """
        返回运镜变化点列表：
        [
          MotionChange(timestamp=8.3, motion_type="pan", magnitude=0.7),
          MotionChange(timestamp=23.1, motion_type="zoom", magnitude=0.9),
        ]
        """
```

使用 `cv2.calcOpticalFlowFarneback` 计算稠密光流，分析全局运动向量：
- **平移 (pan)**：水平/垂直方向一致的大位移
- **推拉 (zoom)**：从中心向外或向内的放射状运动
- **固定**：光流幅度很小
- **剧烈变化点**：连续帧之间光流模式突变

#### VADDetector（人声活动检测）

```python
class VADDetector:
    """基于 Silero VAD 的人声检测"""

    def detect(self, audio_path: str) -> VADResult:
        """
        返回：
        VADResult(
            has_speech=True,
            speech_ratio=0.65,  # 65% 时间有人声
            segments=[
              SpeechSegment(start=0.0, end=15.3),
              SpeechSegment(start=20.1, end=45.8),
            ]
        )
        """
```

选择 Silero VAD 的原因：
- 轻量，CPU 即可运行（比 Whisper 做 VAD 快 10x+）
- 准确区分人声和背景音乐/环境音
- 输出精确的人声时间区间，可用于后续策略切换

### 2.5 融合决策引擎

```python
class FusionStrategy(ABC):
    """融合策略基类"""

    @abstractmethod
    def fuse(self, analysis: AnalysisResult, config: FusionConfig) -> List[CutPoint]:
        """将多维度分析结果融合为切分点列表"""

class SpeechPriorityStrategy(FusionStrategy):
    """有人声策略：语义优先"""
    # 主：语音句子/话题边界
    # 辅：场景变化 + 运镜变化
    # LLM：分析转录文本，识别话题变化点

class VisualPriorityStrategy(FusionStrategy):
    """无人声策略：视觉优先"""
    # 主：场景切换
    # 辅：运镜变化
    # 规则：综合评分

class PostProcessor:
    """通用后处理"""

    def process(self, cut_points: List[CutPoint], config: FusionConfig) -> List[ClipPlan]:
        """
        1. 从切分点生成初始片段列表
        2. 合并过短片段（< min_duration）
        3. 拆分过长片段（> max_duration）
        4. 添加重叠过渡（1-2s）
        5. 应用用户时长偏好
        """
```

### 2.6 AI/LLM 服务设计

```python
class LLMClient:
    """LLM 客户端 - 统一封装 OpenAI/DashScope 调用"""

    def __init__(self):
        # API Key 从环境变量读取
        # 支持 OPENAI_API_KEY 和 DASHSCOPE_API_KEY

    async def call_with_retry(
        self,
        prompt: str,
        input_data: dict,
        max_retries: int = 3,
        timeout: int = 30
    ) -> str:
        """带重试的 LLM 调用（指数退避）"""

class TopicSegmenter:
    """LLM 话题分段器 - 用于有人声视频"""

    def segment(self, transcript: TranscriptData) -> List[TopicBoundary]:
        """
        输入转录文本，输出话题变化点：
        [
          TopicBoundary(timestamp=25.3, topic="餐厅介绍", confidence=0.9),
          TopicBoundary(timestamp=68.7, topic="菜品点评", confidence=0.85),
        ]
        """

class TagGenerator:
    """LLM 标签生成器 - 为每个切片生成多维度标签"""

    def generate(self, clips: List[ClipInfo]) -> List[ClipTags]:
        """
        批量为切片生成标签：
        ClipTags(
            content=["室内", "餐厅"],
            emotion=["平静", "介绍"],
            technical=["固定镜头", "横屏"],
            purpose=["适合开头"]
        )
        """
```

**LLM 调用原则（来自 .windsurfrules）：**
- 所有 LLM 调用封装在 `deepcut/ai/` 下
- 带指数退避重试，最多 3 次
- 超时：普通调用 30s，长分析 120s
- API Key 环境变量注入
- 记录 token 消耗与延迟

---

## 3. 数据模型 (Pydantic)

### 3.1 核心模型

```python
class VideoInfo(BaseModel):
    """视频基本信息（Step 1 输出）"""
    path: Path
    duration: float           # 秒
    resolution: tuple[int, int]  # (width, height)
    orientation: Literal["landscape", "portrait"]
    codec: str
    fps: float
    file_size: int            # bytes
    has_audio: bool

class VADResult(BaseModel):
    """人声检测结果（Step 2 输出）"""
    has_speech: bool
    speech_ratio: float       # 0.0 ~ 1.0
    segments: list[SpeechSegment]

class AnalysisResult(BaseModel):
    """分析结果（Step 3 输出）"""
    scenes: list[SceneChange]
    motions: list[MotionChange]
    transcript: TranscriptData | None  # 仅有人声时存在
    topic_boundaries: list[TopicBoundary] | None

class ClipPlan(BaseModel):
    """切片计划（Step 4 输出）"""
    id: str                   # clip_001
    start_time: float
    end_time: float
    duration: float
    split_reason: str         # speech_topic | scene_change | motion_change
    overlap_prev: float | None
    overlap_next: float | None

class ClipTags(BaseModel):
    """切片多维度标签（Step 6 输出）"""
    content: list[str]
    emotion: list[str]
    technical: list[str]
    purpose: list[str]

class ClipRelationship(BaseModel):
    """切片关系"""
    sequence_index: int
    scene_group: str
    context: ClipContext

class OutputMetadata(BaseModel):
    """最终输出元数据（metadata.json 的结构）"""
    version: str
    source_video: VideoInfo
    config: PipelineConfig
    clips: list[ClipOutput]
    scenes: list[SceneGroup]
```

---

## 4. Next.js Web 层设计（第二阶段）

### 4.1 项目结构

```
web/                                 # Next.js Web 层根目录
├── package.json
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── prisma/
│   └── schema.prisma
│
└── src/
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx
    │   ├── (dashboard)/
    │   │   ├── layout.tsx
    │   │   ├── videos/
    │   │   │   ├── page.tsx          # 视频列表
    │   │   │   └── [id]/page.tsx     # 视频详情 + 切片预览
    │   │   ├── library/
    │   │   │   └── page.tsx          # 全局片段库
    │   │   └── upload/
    │   │       └── page.tsx          # 上传 / 链接获取
    │   └── api/
    │       ├── videos/               # 视频 CRUD
    │       ├── clips/                # 切片管理
    │       ├── library/              # 全局片段库
    │       ├── slice/                # 触发切片（调用 Python 引擎）
    │       └── tasks/                # 任务状态 + SSE
    │
    ├── components/
    │   ├── ui/                       # shadcn/ui
    │   └── features/
    │       ├── VideoUploader.tsx
    │       ├── VideoList.tsx
    │       ├── ClipTimeline.tsx
    │       ├── ClipCard.tsx
    │       ├── LibraryBrowser.tsx     # 全局片段库浏览器
    │       └── TaskProgress.tsx
    │
    ├── lib/
    │   ├── engine-client/            # Python 引擎 HTTP 客户端
    │   │   ├── index.ts
    │   │   └── types.ts
    │   ├── queue/                    # BullMQ 任务队列
    │   ├── storage/                  # 文件存储
    │   └── db/                       # Prisma
    │
    ├── hooks/
    ├── types/
    ├── utils/
    └── stores/                       # Zustand
```

### 4.2 Web UI 页面结构与交互流程（参考 AutoClip）

> **原则**：参考 AutoClip 的主操作形式（页面结构、交互流程），细节按 DeepCut 自身需求设计。

#### 页面结构

| 页面 | 路径 | 说明 | AutoClip 参考 |
|------|------|------|---------------|
| **首页** | `/` | 视频输入区 + 项目卡片网格列表 | ✅ 采纳"输入 + 列表"单页布局 |
| **视频详情** | `/videos/[id]` | 切片结果展示（卡片网格 + 标签筛选） | ✅ 采纳详情页布局 |
| **全局片段库** | `/library` | 跨视频片段浏览、标签筛选、搜索 | 🆕 DeepCut 独有 |
| **设置** | `/settings` | 引擎配置、API Key 管理 | ✅ 参考 |

#### 首页交互流程

```
┌─ 首页 ────────────────────────────────────┐
│                                            │
│  视频输入区（居中卡片，Tab 切换）           │
│  ┌────────────────┬────────────────┐       │
│  │ 📁 文件上传     │ 📺 链接导入    │       │
│  └────────────────┴────────────────┘       │
│  拖拽上传 / 粘贴 URL → 创建项目 → 自动处理  │
│                                            │
│  项目列表（卡片网格 + 状态筛选）+ 全局片段库入口 │
│  ┌──────┐ ┌──────┐ ┌──────┐               │
│  │缩略图│ │缩略图│ │缩略图│               │
│  │项目名│ │项目名│ │项目名│               │
│  │状态条│ │状态条│ │状态条│               │
│  │切片数│ │切片数│ │切片数│               │
│  └──────┘ └──────┘ └──────┘               │
└────────────────────────────────────────────┘
```

#### 核心交互组件

| 组件 | 功能 | 与 AutoClip 差异 |
|------|------|-----------------|
| `VideoUploader` | 拖拽上传 + 分片传输 + 进度条 | 不需要 SRT 上传（自带 Whisper） |
| `LinkImporter` | URL 粘贴 → 解析 → yt-dlp 下载 | 无视频分类选择（VAD 自动判断） |
| `ProjectCard` | 缩略图 + 项目名 + 状态 + 切片数 + 标签预览 | 增加画幅方向标记 |
| `ClipCard` | 缩略图 + 标题 + 摘要 + 多维度标签 + 操作 | 增加标签展示，无评分/投稿 |
| `LibraryBrowser` | 跨视频片段库浏览 + 标签筛选 + 搜索 | 🆕 AutoClip 无此功能 |
| `TaskProgress` | SSE 实时进度推送 | 与 AutoClip 类似 |

### 4.3 Next.js ↔ Python 通信

```
Next.js API Route                 Python FastAPI
      │                                │
      ├─ POST /api/slice ────────────► POST /api/slice
      │  {video_path, config}          {video_path, config}
      │                                │
      │  ◄─── 202 {task_id} ──────────┤
      │                                │  (开始执行 pipeline)
      │                                │
      ├─ GET /api/status/{id} ───────► GET /api/status/{id}
      │  (轮询或 SSE)                  │
      │  ◄─── {status, progress} ──────┤
      │                                │
      │  ◄─── {completed, metadata} ───┤  (pipeline 完成)
      │                                │
      ├─ 读取 metadata.json            │
      ├─ 入库 PostgreSQL               │
      └─ 返回结果给前端                │
```

---

## 5. 目录结构总览

```
DeepCut/
├── .windsurfrules                   # 开发规范
├── SPEC.md                          # 技术规格
├── ARCHITECTURE.md                  # 架构设计 (本文件)
├── TASKS.md                         # 任务清单
├── .gitignore
│
├── engine/                          # Python 切片引擎 ★ MVP 核心
│   ├── pyproject.toml
│   ├── deepcut/
│   │   ├── cli.py
│   │   ├── config.py
│   │   ├── pipeline/               # 7 步流水线
│   │   ├── analyzers/              # 检测模块
│   │   ├── fusion/                 # 融合决策
│   │   ├── ai/                     # LLM 服务
│   │   ├── video/                  # FFmpeg 封装
│   │   ├── models/                 # Pydantic 模型
│   │   └── utils/
│   ├── api/                        # FastAPI (第二阶段)
│   └── tests/
│
├── web/                             # Next.js Web 层（第二阶段）
│   ├── package.json
│   ├── next.config.ts
│   ├── prisma/
│   └── src/
│
└── test-data/                       # 测试视频
    └── silent_scenery.mp4
```

---

## 6. 部署架构

### MVP（本地开发）

```
本地进程:
  └── python -m deepcut.cli --input video.mp4
      (纯 Python，无外部服务依赖)

依赖:
  ├── FFmpeg (系统安装)
  ├── Python 3.11+
  └── OpenAI API Key (环境变量)
```

### 第二阶段（Web 平台）

```
Docker Compose:
  ├── PostgreSQL (port 5432)
  ├── Redis (port 6379)
  ├── Python Engine (FastAPI, port 8000)
  └── Next.js (port 3000)
```

### 生产环境

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Next.js     │     │  Python Engine   │     │  文件存储     │
│  (Vercel/    │◄───►│  (Docker/GPU VM) │────►│  (S3/本地)   │
│   Docker)    │HTTP │  FastAPI + 引擎   │     └──────────────┘
└──────┬───────┘     └────────┬─────────┘
       │                      │
  ┌────▼──────────────────────▼────┐
  │       Managed Services         │
  │  ┌──────────┐ ┌───────────┐    │
  │  │PostgreSQL│ │   Redis   │    │
  │  └──────────┘ └───────────┘    │
  └────────────────────────────────┘
```

---

## 7. 环境变量

```bash
# AI 服务
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1    # 可选，支持代理
DASHSCOPE_API_KEY=sk-...                      # 可选，阿里云备选

# Whisper 模型
WHISPER_MODEL=base                            # tiny/base/small/medium/large
WHISPER_DEVICE=cpu                            # cpu/cuda

# 切片引擎配置
DEEPCUT_DEFAULT_MIN_DURATION=5                # 最小切片时长（秒）
DEEPCUT_DEFAULT_MAX_DURATION=30               # 最大切片时长（秒）
DEEPCUT_OVERLAP_DURATION=1.5                  # 重叠过渡时长（秒）

# 第二阶段
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379
PYTHON_ENGINE_URL=http://localhost:8000
```

---

## 8. 安全设计

| 层面 | MVP | Web 阶段 |
|------|-----|----------|
| **API Key** | 环境变量注入 | 环境变量 + Secret Manager |
| **认证** | N/A（CLI） | NextAuth.js / Clerk |
| **文件访问** | 本地文件系统 | S3 预签名 URL |
| **输入校验** | Pydantic 模型 | Pydantic + Zod |
| **速率限制** | N/A | API 层限流 |
