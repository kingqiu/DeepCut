"""测试 FFmpeg 视频探测"""

from pathlib import Path

import pytest

from deepcut.exceptions import FFmpegError
from deepcut.video.probe import _determine_orientation, _parse_fps, probe_video


class TestParseHelpers:
    def test_parse_fps_fraction(self) -> None:
        assert _parse_fps("30/1") == 30.0
        assert _parse_fps("24000/1001") == pytest.approx(23.976, rel=1e-2)

    def test_parse_fps_float(self) -> None:
        assert _parse_fps("29.97") == pytest.approx(29.97)

    def test_parse_fps_invalid(self) -> None:
        assert _parse_fps("invalid") == 30.0

    def test_parse_fps_zero_denominator(self) -> None:
        assert _parse_fps("30/0") == 30.0

    def test_orientation_landscape(self) -> None:
        assert _determine_orientation(1920, 1080) == "landscape"

    def test_orientation_portrait(self) -> None:
        assert _determine_orientation(1080, 1920) == "portrait"

    def test_orientation_square(self) -> None:
        assert _determine_orientation(1080, 1080) == "square"


class TestProbeVideo:
    def test_nonexistent_file(self) -> None:
        with pytest.raises(FFmpegError, match="不存在"):
            probe_video(Path("/tmp/nonexistent_video_12345.mp4"))

    def test_silent_scenery(self, silent_scenery_path: Path) -> None:
        """探测无人声风景视频"""
        info = probe_video(silent_scenery_path)
        assert info.duration > 0
        assert info.width > 0
        assert info.height > 0
        assert info.fps > 0
        assert info.has_audio is True
        assert info.codec in ("hevc", "h265", "hev1")
        assert info.orientation in ("landscape", "portrait", "square")

    def test_korean_restaurant(self, korean_restaurant_path: Path) -> None:
        """探测有人声探店视频"""
        info = probe_video(korean_restaurant_path)
        assert info.duration > 400  # 8.2 min > 400s
        assert info.has_audio is True
        assert info.codec in ("av1", "av01")
