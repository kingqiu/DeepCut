"""场景检测器：PySceneDetect，检测视频中的场景切换点"""

from pathlib import Path

from loguru import logger

from deepcut.exceptions import SceneDetectionError
from deepcut.models.analysis import SceneChange


class SceneDetector:
    """PySceneDetect 场景检测器

    使用 ContentDetector 检测基于内容变化的场景切换，
    配合 ThresholdDetector 检测淡入淡出。
    """

    def __init__(
        self,
        content_threshold: float = 22.0,
        min_scene_len: float = 1.0,
    ) -> None:
        """
        Args:
            content_threshold: ContentDetector 阈值（越低越敏感，默认 22.0）
            min_scene_len: 最小场景长度（秒），防止过于频繁的切换（默认 1.0）
        """
        self.content_threshold = content_threshold
        self.min_scene_len = min_scene_len

    def detect(self, video_path: Path) -> list[SceneChange]:
        """检测视频中的场景切换点

        Args:
            video_path: 视频文件路径

        Returns:
            场景切换点列表

        Raises:
            SceneDetectionError: 检测失败
        """
        if not video_path.exists():
            raise SceneDetectionError(f"视频文件不存在: {video_path}")

        try:
            from scenedetect import ContentDetector, open_video, SceneManager
        except ImportError as e:
            raise SceneDetectionError(
                "PySceneDetect 未安装，请运行: pip install scenedetect[opencv]"
            ) from e

        try:
            video = open_video(str(video_path))
        except Exception as e:
            raise SceneDetectionError(f"无法打开视频: {e}") from e

        try:
            fps = video.frame_rate
            min_scene_len_frames = int(self.min_scene_len * fps)

            scene_manager = SceneManager()
            scene_manager.add_detector(
                ContentDetector(
                    threshold=self.content_threshold,
                    min_scene_len=min_scene_len_frames,
                )
            )

            logger.debug(
                f"开始场景检测: threshold={self.content_threshold}, "
                f"min_scene_len={self.min_scene_len}s ({min_scene_len_frames} frames)"
            )

            scene_manager.detect_scenes(video, show_progress=False)
            scene_list = scene_manager.get_scene_list()

        except Exception as e:
            raise SceneDetectionError(f"场景检测执行失败: {e}") from e

        # 转换为 SceneChange 模型（取每个场景的起始时间作为切换点）
        changes: list[SceneChange] = []
        for i, (start, _end) in enumerate(scene_list):
            if i == 0:
                continue  # 跳过第一个场景的起始点（视频开头）
            timestamp = start.get_seconds()
            changes.append(
                SceneChange(
                    timestamp=timestamp,
                    scene_type="cut",
                )
            )

        logger.info(f"场景检测完成: {len(changes)} 个切换点, {len(scene_list)} 个场景")

        return changes
