"""测试 Pydantic 数据模型"""

from pathlib import Path

from deepcut.models.analysis import (
    AnalysisResult,
    SceneChange,
    TimeRange,
    TranscriptResult,
    TranscriptSegment,
    VADResult,
    VADSegment,
)
from deepcut.models.clip import ClipMetadata, ClipPlan, ClipTag, ClipTags, OutputMetadata
from deepcut.models.video import VideoInfo


class TestVideoInfo:
    def test_landscape(self) -> None:
        info = VideoInfo(
            path=Path("/tmp/test.mp4"),
            duration=60.0,
            width=1920,
            height=1080,
            fps=30.0,
            codec="h264",
            orientation="landscape",
            file_size=1000000,
        )
        assert info.orientation == "landscape"
        assert info.aspect_ratio == 1920 / 1080

    def test_portrait(self) -> None:
        info = VideoInfo(
            path=Path("/tmp/test.mp4"),
            duration=60.0,
            width=1080,
            height=1920,
            fps=30.0,
            codec="h264",
            orientation="portrait",
            file_size=1000000,
        )
        assert info.orientation == "portrait"
        assert info.aspect_ratio < 1.0


class TestTimeRange:
    def test_duration(self) -> None:
        tr = TimeRange(start=10.0, end=25.0)
        assert tr.duration == 15.0


class TestVADResult:
    def test_has_speech(self) -> None:
        vad = VADResult(
            has_speech=True,
            speech_ratio=0.7,
            segments=[VADSegment(start=0.0, end=5.0, confidence=0.95)],
        )
        assert vad.has_speech is True
        assert len(vad.segments) == 1

    def test_no_speech(self) -> None:
        vad = VADResult(has_speech=False, speech_ratio=0.0)
        assert vad.has_speech is False
        assert len(vad.segments) == 0


class TestTranscriptResult:
    def test_full_text(self) -> None:
        result = TranscriptResult(
            language="zh",
            segments=[
                TranscriptSegment(start=0.0, end=3.0, text="你好"),
                TranscriptSegment(start=3.0, end=6.0, text="世界"),
            ],
        )
        assert result.full_text == "你好 世界"


class TestClipPlan:
    def test_duration(self) -> None:
        plan = ClipPlan(
            index=0,
            start=10.0,
            end=25.0,
            split_reason="scene_change",
        )
        assert plan.duration == 15.0


class TestClipTags:
    def test_get_dimension(self) -> None:
        tags = ClipTags(
            tags=[
                ClipTag(dimension="content", values=["美食", "探店"]),
                ClipTag(dimension="emotion", values=["开心"]),
            ]
        )
        assert tags.get_dimension("content") == ["美食", "探店"]
        assert tags.get_dimension("emotion") == ["开心"]
        assert tags.get_dimension("technical") == []


class TestOutputMetadata:
    def test_serialization(self) -> None:
        metadata = OutputMetadata(
            version="v1_20260228_112300",
            source_video="/tmp/test.mp4",
            source_duration=120.0,
            source_orientation="landscape",
            total_clips=3,
            clips=[
                ClipMetadata(
                    index=0,
                    start=0.0,
                    end=15.0,
                    duration=15.0,
                    file_name="clip_000.mp4",
                    split_reason="scene_change",
                ),
            ],
        )
        assert metadata.total_clips == 3
        assert len(metadata.clips) == 1
        data = metadata.model_dump()
        assert data["version"] == "v1_20260228_112300"
