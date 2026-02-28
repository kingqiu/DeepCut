"""标签生成服务：调用多模态 LLM 为切片批量生成多维度标签

使用 vision 模型分析关键帧图片 + 文本信息，生成准确的画面描述标签。
"""

import base64
import json
import tempfile
from pathlib import Path

from loguru import logger

from deepcut.ai.llm_client import LLMClient
from deepcut.exceptions import LLMError
from deepcut.models.clip import ClipTag, ClipTags
from deepcut.video.extract import extract_frame

PROMPT_PATH = Path(__file__).parent / "prompts" / "tag_generation.txt"

_ALL_DIMENSIONS = ("content", "scene", "object", "action", "emotion", "technical", "purpose")


class TagGenerator:
    """LLM 多维度标签生成服务

    为每个切片生成 7 个维度的标签。
    使用 vision 模型分析关键帧截图，确保画面描述准确。
    """

    def __init__(
        self,
        llm_client: LLMClient,
        vision_model: str = "qwen3-vl-plus",
    ) -> None:
        self.llm_client = llm_client
        self.vision_model = vision_model
        self._prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

    def generate_batch(
        self,
        clips_info: list[dict[str, str | float]],
        video_path: Path | None = None,
    ) -> list[ClipTags]:
        """批量生成标签（一次多模态 LLM 调用）

        Args:
            clips_info: 切片信息列表，每项包含 start, end, split_reason,
                        transcript, motion_types, orientation, topic, summary
            video_path: 源视频路径，用于截取关键帧。为 None 则退化为纯文本模式。

        Returns:
            标签列表，与 clips_info 一一对应
        """
        if not clips_info:
            return []

        # 截取关键帧
        keyframe_b64_list: list[str] = []
        if video_path and video_path.exists():
            keyframe_b64_list = self._extract_keyframes(clips_info, video_path)

        # 构建切片摘要文本
        clips_text = self._build_clips_text(clips_info, has_images=bool(keyframe_b64_list))
        user_prompt = self._prompt_template.replace("{clips_info}", clips_text)

        system_prompt = (
            "你是一个专业的短视频内容标签分析师。"
            "请结合每个切片对应的关键帧截图和文本信息，为每个切片生成准确的多维度标签。"
            "请严格按照 JSON 数组格式输出，不要输出任何其他文字。"
        )

        try:
            if keyframe_b64_list:
                logger.info(f"使用 vision 模型 ({self.vision_model}) 分析 {len(keyframe_b64_list)} 张关键帧")
                response = self.llm_client.chat_with_images(
                    system_prompt=system_prompt,
                    text_prompt=user_prompt,
                    image_base64_list=keyframe_b64_list,
                    model_override=self.vision_model,
                    temperature=0.3,
                    max_tokens=4096,
                    timeout=300.0,
                )
            else:
                logger.info("无关键帧，使用纯文本模式生成标签")
                response = self.llm_client.chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.3,
                    max_tokens=4096,
                    timeout=120.0,
                )
        except Exception as e:
            logger.warning(f"批量标签生成 LLM 调用失败: {e}")
            return [self._default_tags() for _ in clips_info]

        try:
            return self._parse_batch_response(response, len(clips_info))
        except Exception as e:
            logger.warning(f"批量标签解析失败: {e}")
            return [self._default_tags() for _ in clips_info]

    def _extract_keyframes(
        self,
        clips_info: list[dict[str, str | float]],
        video_path: Path,
    ) -> list[str]:
        """为每个切片截取中间帧，返回 base64 编码列表"""
        results: list[str] = []
        with tempfile.TemporaryDirectory(prefix="deepcut_frames_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            for i, info in enumerate(clips_info):
                start = float(info.get("start", 0))
                end = float(info.get("end", 0))
                mid = (start + end) / 2

                frame_path = tmp_path / f"frame_{i:03d}.jpg"
                try:
                    extract_frame(video_path, frame_path, mid, width=512)
                    img_bytes = frame_path.read_bytes()
                    results.append(base64.b64encode(img_bytes).decode("ascii"))
                except Exception as e:
                    logger.warning(f"关键帧截取失败 clip_{i} @ {mid:.1f}s: {e}")
                    results.clear()
                    return results

        logger.info(f"关键帧截取完成: {len(results)} 张")
        return results

    def _build_clips_text(
        self,
        clips_info: list[dict[str, str | float]],
        has_images: bool = False,
    ) -> str:
        """构建切片摘要文本"""
        clips_text_parts: list[str] = []
        for i, info in enumerate(clips_info):
            start = float(info.get("start", 0))
            end = float(info.get("end", 0))
            duration = end - start
            m1, s1 = divmod(int(start), 60)
            m2, s2 = divmod(int(end), 60)

            parts = [f"clip_{i}: {m1}:{s1:02d}-{m2}:{s2:02d} ({duration:.0f}s)"]

            if has_images:
                parts.append(f"  关键帧: 第 {i + 1} 张图片")

            topic = str(info.get("topic", ""))
            if topic:
                parts.append(f"  话题: {topic}")

            summary = str(info.get("summary", ""))
            if summary:
                parts.append(f"  摘要: {summary}")

            transcript = str(info.get("transcript", ""))
            if transcript:
                parts.append(f"  转录: {transcript[:100]}")

            motion = str(info.get("motion_types", ""))
            if motion:
                parts.append(f"  运镜: {motion}")

            parts.append(f"  画幅: {info.get('orientation', 'landscape')}")

            clips_text_parts.append("\n".join(parts))

        return "\n\n".join(clips_text_parts)

    def _parse_batch_response(
        self, response: str, expected_count: int
    ) -> list[ClipTags]:
        """解析批量 LLM JSON 响应"""
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        data = json.loads(json_str)

        if not isinstance(data, list):
            raise ValueError(f"期望 JSON 数组，得到 {type(data).__name__}")

        # 按 clip_index 排序，构建结果
        results: list[ClipTags] = [self._default_tags() for _ in range(expected_count)]

        for item in data:
            idx = int(item.get("clip_index", -1))
            if 0 <= idx < expected_count:
                tags: list[ClipTag] = []
                for dimension in ("content", "scene", "object", "action", "emotion", "technical", "purpose"):
                    values = item.get(dimension, [])
                    if isinstance(values, list) and values:
                        tags.append(
                            ClipTag(
                                dimension=dimension,  # type: ignore[arg-type]
                                values=[str(v) for v in values],
                            )
                        )
                if tags:
                    results[idx] = ClipTags(tags=tags)

        generated = sum(1 for r in results if r.tags and r.tags[0].values != ["未分类"])
        logger.info(f"标签生成完成: {generated}/{expected_count} 个切片")

        return results

    def _default_tags(self) -> ClipTags:
        """返回默认标签（LLM 调用失败时的兜底）"""
        return ClipTags(
            tags=[
                ClipTag(dimension="content", values=["未分类"]),
            ]
        )
