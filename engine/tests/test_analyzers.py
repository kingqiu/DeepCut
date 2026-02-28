"""analyzers/ 单元测试：VAD / Transcriber / SceneDetector / MotionDetector"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from deepcut.analyzers.vad_detector import VADDetector
from deepcut.analyzers.scene_detector import SceneDetector
from deepcut.analyzers.motion_detector import MotionDetector
from deepcut.exceptions import VADError


# ---- VADDetector ----


class TestVADDetector:
    def test_init_defaults(self) -> None:
        detector = VADDetector()
        assert detector.model_size == "base"
        assert detector.device == "cpu"
        assert detector._model is None

    def test_detect_missing_file_raises(self) -> None:
        detector = VADDetector()
        with pytest.raises(VADError, match="不存在"):
            detector.detect(Path("/tmp/nonexistent_audio.wav"))

    def test_detect_with_mock_whisper(self, tmp_path: Path) -> None:
        """使用 mock Whisper 模型测试 VAD 检测逻辑"""
        # 创建一个假 WAV 文件
        import struct
        import wave

        wav_path = tmp_path / "test.wav"
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            # 写 10 秒静音数据
            wf.writeframes(b"\x00\x00" * 16000 * 10)

        detector = VADDetector()

        # Mock Whisper 模型
        mock_seg = MagicMock()
        mock_seg.start = 1.0
        mock_seg.end = 5.0
        mock_seg.text = "这是一段测试语音内容"

        mock_info = MagicMock()
        mock_info.language = "zh"
        mock_info.language_probability = 0.95

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_seg], mock_info)

        detector._model = mock_model

        result = detector.detect(wav_path)
        assert result.has_speech is True
        assert result.speech_ratio > 0.0
        assert len(result.segments) == 1

    def test_detect_no_speech(self, tmp_path: Path) -> None:
        """Whisper 没有转录出文字 → 判定无人声"""
        import wave

        wav_path = tmp_path / "silent.wav"
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"\x00\x00" * 16000 * 10)

        detector = VADDetector()

        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.5

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([], mock_info)

        detector._model = mock_model

        result = detector.detect(wav_path)
        assert result.has_speech is False
        assert result.speech_ratio == 0.0
        assert len(result.segments) == 0


# ---- SceneDetector ----


class TestSceneDetector:
    def test_init(self) -> None:
        detector = SceneDetector()
        assert detector.content_threshold > 0
        assert detector.min_scene_len > 0

    def test_init_custom_params(self) -> None:
        detector = SceneDetector(content_threshold=30.0, min_scene_len=2.0)
        assert detector.content_threshold == 30.0
        assert detector.min_scene_len == 2.0

    def test_detect_missing_file_raises(self) -> None:
        from deepcut.exceptions import SceneDetectionError
        detector = SceneDetector()
        with pytest.raises(SceneDetectionError, match="不存在"):
            detector.detect(Path("/tmp/nonexistent_video.mp4"))

    @patch("scenedetect.open_video")
    @patch("scenedetect.SceneManager")
    @patch("scenedetect.ContentDetector")
    def test_detect_returns_scene_changes(
        self,
        mock_cd_cls: MagicMock,
        mock_sm_cls: MagicMock,
        mock_open_video: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Mock PySceneDetect 返回场景变化列表"""
        fake_video = tmp_path / "video.mp4"
        fake_video.touch()

        mock_video = MagicMock()
        mock_video.frame_rate = 30.0
        mock_open_video.return_value = mock_video

        # 3 个场景 → 2 个切换点
        mock_scene1_start = MagicMock(); mock_scene1_start.get_seconds.return_value = 0.0
        mock_scene1_end = MagicMock(); mock_scene1_end.get_seconds.return_value = 12.5
        mock_scene2_start = MagicMock(); mock_scene2_start.get_seconds.return_value = 12.5
        mock_scene2_end = MagicMock(); mock_scene2_end.get_seconds.return_value = 28.0
        mock_scene3_start = MagicMock(); mock_scene3_start.get_seconds.return_value = 28.0
        mock_scene3_end = MagicMock(); mock_scene3_end.get_seconds.return_value = 45.0

        mock_sm = MagicMock()
        mock_sm.get_scene_list.return_value = [
            (mock_scene1_start, mock_scene1_end),
            (mock_scene2_start, mock_scene2_end),
            (mock_scene3_start, mock_scene3_end),
        ]
        mock_sm_cls.return_value = mock_sm

        detector = SceneDetector()
        scenes = detector.detect(fake_video)

        assert len(scenes) == 2
        assert scenes[0].timestamp == 12.5
        assert scenes[1].timestamp == 28.0

    @patch("scenedetect.open_video")
    @patch("scenedetect.SceneManager")
    @patch("scenedetect.ContentDetector")
    def test_detect_no_scenes(
        self,
        mock_cd_cls: MagicMock,
        mock_sm_cls: MagicMock,
        mock_open_video: MagicMock,
        tmp_path: Path,
    ) -> None:
        fake_video = tmp_path / "video.mp4"
        fake_video.touch()

        mock_video = MagicMock()
        mock_video.frame_rate = 30.0
        mock_open_video.return_value = mock_video

        mock_sm = MagicMock()
        mock_sm.get_scene_list.return_value = [
            (MagicMock(**{"get_seconds.return_value": 0.0}),
             MagicMock(**{"get_seconds.return_value": 60.0})),
        ]
        mock_sm_cls.return_value = mock_sm

        detector = SceneDetector()
        scenes = detector.detect(fake_video)
        assert len(scenes) == 0


# ---- MotionDetector ----


class TestMotionDetector:
    def test_init_defaults(self) -> None:
        detector = MotionDetector()
        assert detector.sample_fps > 0
        assert detector.motion_threshold > 0
        assert detector.transition_threshold > 0
        assert detector.min_segment_duration > 0

    def test_init_custom_params(self) -> None:
        detector = MotionDetector(
            sample_fps=10.0, motion_threshold=3.0,
            transition_threshold=20.0, min_segment_duration=2.0,
        )
        assert detector.sample_fps == 10.0
        assert detector.motion_threshold == 3.0

    def test_detect_missing_file_raises(self) -> None:
        from deepcut.exceptions import MotionDetectionError
        detector = MotionDetector()
        with pytest.raises(MotionDetectionError):
            detector.detect(Path("/tmp/nonexistent_video.mp4"))
