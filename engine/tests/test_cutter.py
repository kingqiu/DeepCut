"""video/cutter.py 单元测试"""

from deepcut.video.cutter import format_clip_filename


class TestFormatClipFilename:
    def test_small_total(self) -> None:
        assert format_clip_filename(0, 10) == "clip_000.mp4"
        assert format_clip_filename(9, 10) == "clip_009.mp4"

    def test_medium_total(self) -> None:
        assert format_clip_filename(0, 150) == "clip_000.mp4"
        assert format_clip_filename(99, 150) == "clip_099.mp4"
        assert format_clip_filename(149, 150) == "clip_149.mp4"

    def test_large_total(self) -> None:
        assert format_clip_filename(0, 1000) == "clip_0000.mp4"
        assert format_clip_filename(999, 1000) == "clip_0999.mp4"
