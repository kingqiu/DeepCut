"""融合决策引擎：根据 VAD 结果选择策略，生成切片计划"""

from loguru import logger

from deepcut.fusion.strategy import FusionStrategy, SpeechFirstStrategy, VisualFirstStrategy
from deepcut.models.analysis import AnalysisResult
from deepcut.models.clip import ClipPlan
from deepcut.models.video import VideoInfo


class FusionEngine:
    """融合决策引擎

    根据 VAD 检测结果自动选择融合策略：
    - 有人声 → SpeechFirstStrategy（语义优先）
    - 无人声 → VisualFirstStrategy（视觉优先）
    """

    def __init__(
        self,
        speech_strategy: FusionStrategy | None = None,
        visual_strategy: FusionStrategy | None = None,
    ) -> None:
        self.speech_strategy = speech_strategy or SpeechFirstStrategy()
        self.visual_strategy = visual_strategy or VisualFirstStrategy()

    def decide_and_fuse(
        self,
        video_info: VideoInfo,
        analysis: AnalysisResult,
        min_duration: float = 5.0,
        max_duration: float = 30.0,
        overlap_duration: float = 1.5,
        force_visual: bool = False,
    ) -> list[ClipPlan]:
        """根据分析结果自动选择策略并生成切片计划

        Args:
            video_info: 视频基本信息
            analysis: 综合分析结果
            min_duration: 最小切片时长参考值
            max_duration: 最大切片时长参考值
            overlap_duration: 重叠过渡时长
            force_visual: 强制使用视觉优先策略（--no-speech）

        Returns:
            切片计划列表
        """
        # 选择策略
        if force_visual or not analysis.vad.has_speech:
            strategy = self.visual_strategy
            strategy_name = "视觉优先 (VisualFirst)"
            reason = "强制视觉模式" if force_visual else f"无人声 (speech_ratio={analysis.vad.speech_ratio:.1%})"
        else:
            strategy = self.speech_strategy
            strategy_name = "语义优先 (SpeechFirst)"
            reason = f"有人声 (speech_ratio={analysis.vad.speech_ratio:.1%})"

        logger.info(f"融合策略: {strategy_name} ({reason})")

        # 执行融合
        clip_plans = strategy.fuse(
            video_info=video_info,
            analysis=analysis,
            min_duration=min_duration,
            max_duration=max_duration,
            overlap_duration=overlap_duration,
        )

        # 分配场景组
        clip_plans = self._assign_scene_groups(clip_plans, analysis)

        logger.info(
            f"融合完成: {len(clip_plans)} 个切片, "
            f"时长范围 {self._format_duration_range(clip_plans)}"
        )

        return clip_plans

    def _assign_scene_groups(
        self, clips: list[ClipPlan], analysis: AnalysisResult
    ) -> list[ClipPlan]:
        """为切片分配场景组编号"""
        if not analysis.scenes:
            return clips

        scene_boundaries = [s.timestamp for s in analysis.scenes]
        current_group = 0

        for clip in clips:
            clip_mid = (clip.start + clip.end) / 2
            group = 0
            for boundary in scene_boundaries:
                if clip_mid > boundary:
                    group += 1
            clip.scene_group = group

        return clips

    def _format_duration_range(self, clips: list[ClipPlan]) -> str:
        """格式化切片时长范围"""
        if not clips:
            return "N/A"
        durations = [c.duration for c in clips]
        return f"{min(durations):.1f}s ~ {max(durations):.1f}s (avg {sum(durations)/len(durations):.1f}s)"
