"""自定义异常类层级"""


class DeepCutError(Exception):
    """DeepCut 基础异常"""


class FFmpegError(DeepCutError):
    """FFmpeg 调用失败"""


class AnalysisError(DeepCutError):
    """分析器执行失败"""


class VADError(AnalysisError):
    """VAD 检测失败"""


class SceneDetectionError(AnalysisError):
    """场景检测失败"""


class MotionDetectionError(AnalysisError):
    """运镜检测失败"""


class TranscriptionError(AnalysisError):
    """语音转录失败"""


class LLMError(DeepCutError):
    """LLM 调用失败"""


class LLMTimeoutError(LLMError):
    """LLM 调用超时"""


class LLMRateLimitError(LLMError):
    """LLM 速率限制"""


class FusionError(DeepCutError):
    """融合决策失败"""


class PipelineError(DeepCutError):
    """Pipeline 执行失败"""

    def __init__(self, step: str, message: str) -> None:
        self.step = step
        super().__init__(f"[{step}] {message}")
