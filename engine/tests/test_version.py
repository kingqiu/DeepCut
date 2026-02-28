"""测试版本目录管理"""

from pathlib import Path

from deepcut.utils.version import create_version_dir, get_next_version_tag


class TestVersionTag:
    def test_first_version(self, tmp_path: Path) -> None:
        tag = get_next_version_tag(tmp_path)
        assert tag.startswith("v1_")

    def test_increments(self, tmp_path: Path) -> None:
        (tmp_path / "v1_20260101_000000").mkdir()
        (tmp_path / "v2_20260102_000000").mkdir()
        tag = get_next_version_tag(tmp_path)
        assert tag.startswith("v3_")

    def test_nonexistent_base(self, tmp_path: Path) -> None:
        tag = get_next_version_tag(tmp_path / "nonexistent")
        assert tag.startswith("v1_")


class TestCreateVersionDir:
    def test_creates_structure(self, tmp_path: Path) -> None:
        fake_video = tmp_path / "videos" / "test.mp4"
        fake_video.parent.mkdir(parents=True)
        fake_video.touch()

        version_dir = create_version_dir(fake_video)

        assert version_dir.exists()
        assert (version_dir / "clips").exists()
        assert version_dir.parent.name == "deepcut_output"
        assert version_dir.name.startswith("v1_")

    def test_custom_output_dir(self, tmp_path: Path) -> None:
        fake_video = tmp_path / "test.mp4"
        fake_video.touch()
        custom_output = tmp_path / "custom_out"

        version_dir = create_version_dir(fake_video, output_dir=custom_output)

        assert "custom_out" in str(version_dir)
        assert (version_dir / "clips").exists()
