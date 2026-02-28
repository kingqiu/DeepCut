"""video/utils.py 单元测试"""

from deepcut.video.utils import (
    format_duration,
    hms_to_seconds,
    sanitize_filename,
    seconds_to_hms,
)


class TestSecondsToHms:
    def test_zero(self) -> None:
        assert seconds_to_hms(0) == "00:00:00.000"

    def test_fractional(self) -> None:
        assert seconds_to_hms(1.5) == "00:00:01.500"

    def test_minutes(self) -> None:
        assert seconds_to_hms(90.25) == "00:01:30.250"

    def test_hours(self) -> None:
        assert seconds_to_hms(3661.5) == "01:01:01.500"


class TestHmsToSeconds:
    def test_basic(self) -> None:
        assert hms_to_seconds("01:01:01.500") == 3661.5

    def test_zero(self) -> None:
        assert hms_to_seconds("00:00:00.000") == 0.0

    def test_comma_separator(self) -> None:
        assert hms_to_seconds("00:01:30,250") == 90.25

    def test_roundtrip(self) -> None:
        for val in [0.0, 1.5, 90.25, 3661.5, 7200.0]:
            assert abs(hms_to_seconds(seconds_to_hms(val)) - val) < 0.001

    def test_invalid_format(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            hms_to_seconds("invalid")


class TestFormatDuration:
    def test_seconds_only(self) -> None:
        assert format_duration(30.0) == "30s"

    def test_minutes_seconds(self) -> None:
        assert format_duration(65.5) == "1m05s"

    def test_hours(self) -> None:
        assert format_duration(3661.0) == "1h01m01s"

    def test_zero(self) -> None:
        assert format_duration(0.0) == "0s"


class TestSanitizeFilename:
    def test_safe_name(self) -> None:
        assert sanitize_filename("test_video") == "test_video"

    def test_unsafe_chars(self) -> None:
        assert sanitize_filename('测试/视频:名称') == "测试_视频_名称"

    def test_max_length(self) -> None:
        result = sanitize_filename("a" * 200, max_length=50)
        assert len(result) == 50

    def test_empty_becomes_unnamed(self) -> None:
        assert sanitize_filename("...") == "unnamed"

    def test_strips_dots_and_spaces(self) -> None:
        assert sanitize_filename(" .test. ") == "test"
