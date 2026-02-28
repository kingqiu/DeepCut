# DeepCut Engine - 智能短视频切片引擎

多模态 AI 驱动的视频切片引擎，支持有人声（语义优先）和无人声（视觉优先）两种切片策略。

## 快速开始

```bash
# 安装依赖
uv pip install -e ".[dev]"

# 运行切片
deepcut /path/to/video.mp4

# 查看帮助
deepcut --help
```

## 系统依赖

- Python 3.11+
- FFmpeg 6.0+
- OpenAI API Key（环境变量 `OPENAI_API_KEY`）

## 配置

复制 `.env.example` 为 `.env`，填入 API Key：

```bash
cp .env.example .env
```
