"""人声检测器：基于 faster-whisper 试探转录判断有无人声

参考 AutoClip 的实现思路：不使用独立 VAD 模型，
而是直接用 Whisper 转录来判断是否有人声。
Whisper 对低音量音频鲁棒性远好于 Silero VAD。
"""

from pathlib import Path

from loguru import logger

from deepcut.exceptions import VADError
from deepcut.models.analysis import VADResult, VADSegment

# 试探转录的采样时长（秒）：取视频前 60s 做快速判断
PROBE_DURATION = 60.0
# 人声判定阈值：试探区间内转录出的文字字数
MIN_CHARS_FOR_SPEECH = 5
# speech_ratio 判定阈值
SPEECH_RATIO_THRESHOLD = 0.05


class VADDetector:
    """基于 Whisper 的人声检测器

    策略：用 faster-whisper 对音频前 N 秒做快速转录试探，
    如果转录出有效文字则判定有人声。比 Silero VAD 对低音量音频更鲁棒。

    当 Pipeline 后续步骤需要完整转录时，VAD 阶段的试探结果会被丢弃，
    由 Transcriber 重新做完整转录，不会造成重复。
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        probe_duration: float = PROBE_DURATION,
    ) -> None:
        """
        Args:
            model_size: Whisper 模型大小
            device: 推理设备
            compute_type: 计算类型
            probe_duration: 试探转录的时长（秒）
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.probe_duration = probe_duration
        self._model = None

    def _load_model(self):  # type: ignore[no-untyped-def]
        """延迟加载 faster-whisper 模型"""
        if self._model is None:
            from faster_whisper import WhisperModel

            logger.debug(f"加载 Whisper 模型 (VAD): {self.model_size}")
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            logger.debug("Whisper 模型加载完成 (VAD)")
        return self._model

    def detect(self, audio_path: Path) -> VADResult:
        """对音频文件执行人声检测

        Args:
            audio_path: WAV 音频文件路径

        Returns:
            VADResult 包含 has_speech、speech_ratio 和粗粒度 segments

        Raises:
            VADError: 检测失败
        """
        if not audio_path.exists():
            raise VADError(f"音频文件不存在: {audio_path}")

        try:
            model = self._load_model()
        except Exception as e:
            raise VADError(f"Whisper 模型加载失败: {e}") from e

        try:
            segments_gen, info = model.transcribe(
                str(audio_path),
                beam_size=1,
                best_of=1,
                language=None,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200,
                ),
            )

            # 收集片段（仅取 probe_duration 范围内）
            segments: list[VADSegment] = []
            total_speech_chars = 0
            max_end = 0.0

            for seg in segments_gen:
                text = seg.text.strip()
                if not text:
                    continue

                # 记录人声区间
                segments.append(
                    VADSegment(
                        start=seg.start,
                        end=seg.end,
                        confidence=1.0,
                    )
                )
                total_speech_chars += len(text)
                max_end = max(max_end, seg.end)

                # 试探阶段只需前 probe_duration 秒的数据来判断
                # 但我们不 break，让 Whisper 跑完以获得完整 speech_ratio
                # faster-whisper 自带 VAD 过滤，非语音区域会很快跳过

        except Exception as e:
            raise VADError(f"Whisper 试探转录失败: {e}") from e

        # 计算人声占比
        speech_duration = sum(seg.end - seg.start for seg in segments)
        # 估算总时长（从文件信息或最后片段）
        total_duration = max(max_end, 1.0)

        # 用 wave 获取准确时长
        try:
            import wave
            with wave.open(str(audio_path), "rb") as wf:
                total_duration = wf.getnframes() / wf.getframerate()
        except Exception:
            pass

        speech_ratio = speech_duration / total_duration if total_duration > 0 else 0.0

        has_speech = (
            total_speech_chars >= MIN_CHARS_FOR_SPEECH
            and speech_ratio > SPEECH_RATIO_THRESHOLD
        )

        logger.info(
            f"人声检测完成 (Whisper): has_speech={has_speech}, "
            f"speech_ratio={speech_ratio:.1%}, "
            f"segments={len(segments)}, chars={total_speech_chars}, "
            f"lang={info.language} (p={info.language_probability:.2f})"
        )

        return VADResult(
            has_speech=has_speech,
            speech_ratio=min(speech_ratio, 1.0),
            segments=segments,
        )
