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

    def test_project_id_mode(self, tmp_path: Path) -> None:
        """Web 模式：output_dir + project_id → {output_dir}/{project_id}/"""
        fake_video = tmp_path / "test.mp4"
        fake_video.touch()
        output_dir = tmp_path / "output"

        version_dir = create_version_dir(
            fake_video, output_dir=output_dir, project_id="abc123"
        )

        assert version_dir == output_dir / "abc123"
        assert version_dir.exists()
        assert (version_dir / "clips").exists()
        assert (version_dir / "thumbnails").exists()

    def test_project_id_without_output_dir_falls_back(self, tmp_path: Path) -> None:
        """project_id 没有 output_dir 时走 CLI 模式"""
        fake_video = tmp_path / "test.mp4"
        fake_video.touch()

        version_dir = create_version_dir(fake_video, project_id="abc123")

        # 无 output_dir 时 project_id 被忽略，走 CLI 版本目录模式
        assert version_dir.parent.name == "deepcut_output"
        assert version_dir.name.startswith("v1_")

    def test_thumbnails_dir_created(self, tmp_path: Path) -> None:
        fake_video = tmp_path / "test.mp4"
        fake_video.touch()

        version_dir = create_version_dir(fake_video)
        assert (version_dir / "thumbnails").exists()
