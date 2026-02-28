"""fusion/ 单元测试：策略模式 + 融合引擎"""

from pathlib import Path

from deepcut.fusion.engine import FusionEngine
from deepcut.fusion.strategy import SpeechFirstStrategy, VisualFirstStrategy
from deepcut.models.analysis import (
    AnalysisResult,
    MotionChange,
    SceneChange,
    TranscriptResult,
    TranscriptSegment,
    VADResult,
    VADSegment,
)
from deepcut.models.video import VideoInfo


def _make_video_info(duration: float = 60.0) -> VideoInfo:
    return VideoInfo(
        path=Path("/tmp/fake_video.mp4"),
        duration=duration,
        width=1920,
        height=1080,
        fps=30.0,
        codec="h264",
        has_audio=True,
        orientation="landscape",
        file_size=1024 * 1024,
    )


def _make_speech_analysis(duration: float = 60.0) -> AnalysisResult:
    """模拟有人声的分析结果"""
    return AnalysisResult(
        vad=VADResult(
            has_speech=True,
            speech_ratio=0.9,
            segments=[VADSegment(start=0.0, end=duration, confidence=1.0)],
        ),
        transcript=TranscriptResult(
            language="zh",
            segments=[
                TranscriptSegment(start=0.0, end=8.0, text="这是第一句话"),
                TranscriptSegment(start=8.5, end=16.0, text="这是第二句话"),
                TranscriptSegment(start=16.5, end=25.0, text="这是第三句话"),
                TranscriptSegment(start=25.5, end=35.0, text="这是第四句话"),
                TranscriptSegment(start=35.5, end=45.0, text="这是第五句话"),
                TranscriptSegment(start=45.5, end=55.0, text="这是第六句话"),
                TranscriptSegment(start=55.5, end=duration, text="最后一句"),
            ],
        ),
        scenes=[
            SceneChange(timestamp=20.0),
            SceneChange(timestamp=40.0),
        ],
        motions=[],
        topics=[],
    )


def _make_visual_analysis(duration: float = 60.0) -> AnalysisResult:
    """模拟无人声的分析结果"""
    return AnalysisResult(
        vad=VADResult(has_speech=False, speech_ratio=0.0),
        transcript=None,
        scenes=[
            SceneChange(timestamp=12.0),
            SceneChange(timestamp=25.0),
            SceneChange(timestamp=38.0),
            SceneChange(timestamp=50.0),
        ],
        motions=[
            MotionChange(start=0.0, end=10.0, motion_type="pan", intensity=0.6),
            MotionChange(start=12.0, end=22.0, motion_type="static", intensity=0.1),
            MotionChange(start=25.0, end=35.0, motion_type="zoom", intensity=0.5),
            MotionChange(start=38.0, end=48.0, motion_type="transition", intensity=0.9),
        ],
        topics=[],
    )


# ---- SpeechFirstStrategy ----


class TestSpeechFirstStrategy:
    def test_produces_clips(self) -> None:
        strategy = SpeechFirstStrategy()
        video_info = _make_video_info(60.0)
        analysis = _make_speech_analysis(60.0)
        clips = strategy.fuse(video_info, analysis, 5.0, 30.0, 1.5)
        assert len(clips) > 0

    def test_clips_cover_video(self) -> None:
        strategy = SpeechFirstStrategy()
        video_info = _make_video_info(60.0)
        analysis = _make_speech_analysis(60.0)
        clips = strategy.fuse(video_info, analysis, 5.0, 30.0, 1.5)
        # 第一个切片从 0 开始
        assert clips[0].start == 0.0
        # 最后一个切片接近视频末尾
        assert clips[-1].end >= 55.0

    def test_split_reason_set(self) -> None:
        strategy = SpeechFirstStrategy()
        video_info = _make_video_info(60.0)
        analysis = _make_speech_analysis(60.0)
        clips = strategy.fuse(video_info, analysis, 5.0, 30.0, 1.5)
        for clip in clips:
            assert clip.split_reason != ""

    def test_first_clip_no_prev_overlap(self) -> None:
        strategy = SpeechFirstStrategy()
        video_info = _make_video_info(60.0)
        analysis = _make_speech_analysis(60.0)
        clips = strategy.fuse(video_info, analysis, 5.0, 30.0, 1.5)
        assert clips[0].overlap_prev == 0.0


# ---- VisualFirstStrategy ----


class TestVisualFirstStrategy:
    def test_produces_clips(self) -> None:
        strategy = VisualFirstStrategy()
        video_info = _make_video_info(60.0)
        analysis = _make_visual_analysis(60.0)
        clips = strategy.fuse(video_info, analysis, 5.0, 30.0, 1.5)
        assert len(clips) > 0

    def test_scene_based_splitting(self) -> None:
        strategy = VisualFirstStrategy()
        video_info = _make_video_info(60.0)
        analysis = _make_visual_analysis(60.0)
        clips = strategy.fuse(video_info, analysis, 5.0, 30.0, 1.5)
        reasons = {c.split_reason for c in clips}
        # 应该包含场景切换或运镜相关的原因
        assert any("scene" in r or "motion" in r or "video" in r for r in reasons)

    def test_fallback_fixed_interval(self) -> None:
        """场景太少时应补充固定间隔"""
        strategy = VisualFirstStrategy()
        video_info = _make_video_info(120.0)
        # 只有 1 个场景切换点 → 太少
        analysis = AnalysisResult(
            vad=VADResult(has_speech=False, speech_ratio=0.0),
            transcript=None,
            scenes=[SceneChange(timestamp=60.0)],
            motions=[],
            topics=[],
        )
        clips = strategy.fuse(video_info, analysis, 5.0, 30.0, 1.5)
        assert len(clips) >= 2  # 120s with few scenes should still produce clips


# ---- FusionEngine ----


class TestFusionEngine:
    def test_selects_speech_first(self) -> None:
        engine = FusionEngine()
        video_info = _make_video_info(60.0)
        analysis = _make_speech_analysis(60.0)

        clips = engine.decide_and_fuse(
            video_info=video_info,
            analysis=analysis,
            min_duration=5.0,
            max_duration=30.0,
            overlap_duration=1.5,
        )
        assert len(clips) > 0

    def test_selects_visual_first(self) -> None:
        engine = FusionEngine()
        video_info = _make_video_info(60.0)
        analysis = _make_visual_analysis(60.0)

        clips = engine.decide_and_fuse(
            video_info=video_info,
            analysis=analysis,
            min_duration=5.0,
            max_duration=30.0,
            overlap_duration=1.5,
        )
        assert len(clips) > 0

    def test_force_visual(self) -> None:
        engine = FusionEngine()
        video_info = _make_video_info(60.0)
        # Use speech analysis but force visual
        analysis = _make_speech_analysis(60.0)

        clips = engine.decide_and_fuse(
            video_info=video_info,
            analysis=analysis,
            min_duration=5.0,
            max_duration=30.0,
            overlap_duration=1.5,
            force_visual=True,
        )
        assert len(clips) > 0
