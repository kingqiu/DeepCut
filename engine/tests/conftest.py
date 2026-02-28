"""测试 fixtures：测试视频路径等共享资源"""

from pathlib import Path

import pytest


# 测试视频路径
TEST_DATA_DIR = Path(__file__).parent.parent.parent / "test-data"

# 有人声测试视频
KOREAN_RESTAURANT = Path("/Users/azhua/Downloads/docker/autoclip/data/uploads/korean_restaurant.mp4")
TEST_VIDEO = Path("/Users/azhua/Downloads/docker/autoclip/data/uploads/test_video.mp4")

# 无人声测试视频
SILENT_SCENERY = TEST_DATA_DIR / "silent_scenery.mp4"


@pytest.fixture
def silent_scenery_path() -> Path:
    """无人声风景视频（3.2min, HEVC+AAC）"""
    if not SILENT_SCENERY.exists():
        pytest.skip(f"测试视频不存在: {SILENT_SCENERY}")
    return SILENT_SCENERY


@pytest.fixture
def korean_restaurant_path() -> Path:
    """有人声探店视频（8.2min, AV1+AAC）"""
    if not KOREAN_RESTAURANT.exists():
        pytest.skip(f"测试视频不存在: {KOREAN_RESTAURANT}")
    return KOREAN_RESTAURANT


@pytest.fixture
def test_video_path() -> Path:
    """有人声探房视频（9.9min, H.264+AAC）"""
    if not TEST_VIDEO.exists():
        pytest.skip(f"测试视频不存在: {TEST_VIDEO}")
    return TEST_VIDEO


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """临时输出目录"""
    output = tmp_path / "deepcut_output"
    output.mkdir()
    return output
