"""语音转录器：faster-whisper，带时间戳转录，支持中英混合"""

from pathlib import Path

from loguru import logger

from deepcut.exceptions import TranscriptionError
from deepcut.models.analysis import TranscriptResult, TranscriptSegment


class Transcriber:
    """faster-whisper 语音转录器

    对音频执行语音识别，输出带时间戳的文本片段。
    支持中英混合语音识别。
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        """
        Args:
            model_size: 模型大小 tiny/base/small/medium/large-v3
            device: 推理设备 cpu/cuda
            compute_type: 计算类型 float16/int8
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _load_model(self):  # type: ignore[no-untyped-def]
        """延迟加载 faster-whisper 模型"""
        if self._model is None:
            from faster_whisper import WhisperModel

            logger.debug(
                f"加载 Whisper 模型: {self.model_size} "
                f"(device={self.device}, compute_type={self.compute_type})"
            )
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            logger.debug("Whisper 模型加载完成")
        return self._model

    def transcribe(self, audio_path: Path) -> TranscriptResult:
        """转录音频文件

        Args:
            audio_path: WAV 音频文件路径

        Returns:
            TranscriptResult 包含语言和带时间戳的文本片段

        Raises:
            TranscriptionError: 转录失败
        """
        if not audio_path.exists():
            raise TranscriptionError(f"音频文件不存在: {audio_path}")

        try:
            model = self._load_model()
        except Exception as e:
            raise TranscriptionError(f"Whisper 模型加载失败: {e}") from e

        try:
            logger.debug(f"开始转录: {audio_path}")

            segments_gen, info = model.transcribe(
                str(audio_path),
                beam_size=5,
                language=None,  # 自动检测语言
                vad_filter=True,  # 使用 VAD 过滤静音段
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200,
                ),
            )

            detected_language = info.language
            logger.info(f"检测到语言: {detected_language} (概率: {info.language_probability:.2f})")

            # 收集所有片段
            transcript_segments: list[TranscriptSegment] = []
            for segment in segments_gen:
                text = segment.text.strip()
                if not text:
                    continue
                transcript_segments.append(
                    TranscriptSegment(
                        start=segment.start,
                        end=segment.end,
                        text=text,
                        language=detected_language,
                    )
                )

            logger.info(
                f"转录完成: {len(transcript_segments)} 个片段, "
                f"语言={detected_language}"
            )

            return TranscriptResult(
                language=detected_language,
                segments=transcript_segments,
            )

        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(f"语音转录失败: {e}") from e
