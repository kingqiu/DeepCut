"""运镜检测器：OpenCV 稠密光流分析，识别运镜类型和突变"""

from pathlib import Path

import cv2
import numpy as np
from loguru import logger

from deepcut.exceptions import MotionDetectionError
from deepcut.models.analysis import MotionChange


class MotionDetector:
    """OpenCV 稠密光流运镜检测器

    通过 Farnebäck 光流分析视频中的运动模式，
    识别平移(pan)、倾斜(tilt)、推拉(zoom)、静止(static)、抖动(shake)和突变(transition)。
    """

    def __init__(
        self,
        sample_fps: float = 5.0,
        motion_threshold: float = 2.0,
        transition_threshold: float = 15.0,
        min_segment_duration: float = 1.0,
    ) -> None:
        """
        Args:
            sample_fps: 采样帧率（降低帧率以加速处理）
            motion_threshold: 运动判定阈值（像素位移均值）
            transition_threshold: 突变判定阈值（远大于正常运动）
            min_segment_duration: 最小运镜段时长（秒）
        """
        self.sample_fps = sample_fps
        self.motion_threshold = motion_threshold
        self.transition_threshold = transition_threshold
        self.min_segment_duration = min_segment_duration

    def detect(self, video_path: Path) -> list[MotionChange]:
        """检测视频中的运镜变化

        Args:
            video_path: 视频文件路径

        Returns:
            运镜变化区间列表

        Raises:
            MotionDetectionError: 检测失败
        """
        if not video_path.exists():
            raise MotionDetectionError(f"视频文件不存在: {video_path}")

        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise MotionDetectionError(f"无法打开视频: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            # 计算采样间隔
            frame_interval = max(1, int(fps / self.sample_fps))

            logger.debug(
                f"运镜检测: fps={fps:.1f}, total_frames={total_frames}, "
                f"duration={duration:.1f}s, sample_interval={frame_interval}"
            )

            # 收集光流数据
            flow_data = self._compute_optical_flow(cap, frame_interval, fps)

        except MotionDetectionError:
            raise
        except Exception as e:
            raise MotionDetectionError(f"运镜检测执行失败: {e}") from e
        finally:
            if "cap" in locals():
                cap.release()

        if not flow_data:
            logger.warning("未检测到有效光流数据")
            return []

        # 分析运动模式
        segments = self._classify_motion(flow_data)

        # 合并相邻同类型的段落
        merged = self._merge_segments(segments)

        logger.info(f"运镜检测完成: {len(merged)} 个运镜段")
        return merged

    def _compute_optical_flow(
        self,
        cap: cv2.VideoCapture,
        frame_interval: int,
        fps: float,
    ) -> list[dict[str, float]]:
        """计算逐帧光流数据"""
        flow_data: list[dict[str, float]] = []
        prev_gray = None
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval != 0:
                frame_idx += 1
                continue

            # 缩放到较小尺寸以加速
            small = cv2.resize(frame, (320, 180))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

            if prev_gray is not None:
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, gray,
                    None,  # type: ignore[arg-type]
                    pyr_scale=0.5,
                    levels=3,
                    winsize=15,
                    iterations=3,
                    poly_n=5,
                    poly_sigma=1.2,
                    flags=0,
                )

                # 提取光流特征
                dx = flow[..., 0]  # 水平位移
                dy = flow[..., 1]  # 垂直位移
                magnitude = np.sqrt(dx**2 + dy**2)

                timestamp = frame_idx / fps

                flow_data.append({
                    "timestamp": timestamp,
                    "mean_mag": float(np.mean(magnitude)),
                    "max_mag": float(np.max(magnitude)),
                    "mean_dx": float(np.mean(dx)),
                    "mean_dy": float(np.mean(dy)),
                    "std_mag": float(np.std(magnitude)),
                })

            prev_gray = gray
            frame_idx += 1

        return flow_data

    def _classify_motion(
        self, flow_data: list[dict[str, float]]
    ) -> list[MotionChange]:
        """根据光流特征分类运镜类型"""
        segments: list[MotionChange] = []

        for i, data in enumerate(flow_data):
            mean_mag = data["mean_mag"]
            mean_dx = data["mean_dx"]
            mean_dy = data["mean_dy"]
            std_mag = data["std_mag"]
            timestamp = data["timestamp"]

            # 估算时间区间
            if i + 1 < len(flow_data):
                next_ts = flow_data[i + 1]["timestamp"]
            else:
                next_ts = timestamp + (1.0 / self.sample_fps)

            # 分类
            if mean_mag > self.transition_threshold:
                motion_type = "transition"
                intensity = min(1.0, mean_mag / (self.transition_threshold * 2))
            elif mean_mag < self.motion_threshold:
                motion_type = "static"
                intensity = 0.1
            elif std_mag > mean_mag * 0.8:
                motion_type = "shake"
                intensity = min(1.0, mean_mag / self.transition_threshold)
            elif abs(mean_dx) > abs(mean_dy) * 2:
                motion_type = "pan"
                intensity = min(1.0, abs(mean_dx) / 10.0)
            elif abs(mean_dy) > abs(mean_dx) * 2:
                motion_type = "tilt"
                intensity = min(1.0, abs(mean_dy) / 10.0)
            else:
                motion_type = "zoom"
                intensity = min(1.0, mean_mag / 10.0)

            segments.append(
                MotionChange(
                    start=timestamp,
                    end=next_ts,
                    motion_type=motion_type,  # type: ignore[arg-type]
                    intensity=intensity,
                )
            )

        return segments

    def _merge_segments(self, segments: list[MotionChange]) -> list[MotionChange]:
        """合并相邻同类型的运镜段落"""
        if not segments:
            return []

        merged: list[MotionChange] = [segments[0]]

        for seg in segments[1:]:
            prev = merged[-1]
            if prev.motion_type == seg.motion_type:
                merged[-1] = MotionChange(
                    start=prev.start,
                    end=seg.end,
                    motion_type=prev.motion_type,
                    intensity=max(prev.intensity, seg.intensity),
                )
            else:
                merged.append(seg)

        # 过滤过短的段落
        result = [
            seg for seg in merged
            if (seg.end - seg.start) >= self.min_segment_duration
        ]

        return result
