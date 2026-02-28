"""话题分段服务：调用 LLM 将转录文本分割为话题段落"""

import json
from pathlib import Path

from loguru import logger

from deepcut.ai.llm_client import LLMClient
from deepcut.exceptions import LLMError
from deepcut.models.analysis import TopicSegment, TranscriptResult

PROMPT_PATH = Path(__file__).parent / "prompts" / "topic_segmentation.txt"


class TopicSegmenter:
    """LLM 话题分段服务

    将转录文本输入 LLM，输出话题段落列表。
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client
        self._prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

    def segment(self, transcript: TranscriptResult) -> list[TopicSegment]:
        """将转录文本分段为话题

        Args:
            transcript: 转录结果

        Returns:
            话题段落列表

        Raises:
            LLMError: LLM 调用或解析失败
        """
        if not transcript.segments:
            logger.warning("转录文本为空，跳过话题分段")
            return []

        # 构建带时间戳的转录文本
        transcript_text = self._format_transcript(transcript)

        user_prompt = self._prompt_template.replace("{transcript}", transcript_text)

        logger.debug(f"话题分段: 输入 {len(transcript.segments)} 个转录片段")

        try:
            response = self.llm_client.chat(
                system_prompt="你是一位专业的视频内容结构分析师。请严格按照 JSON 格式输出话题分段结果，不要输出任何其他文字。",
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=8192,
                timeout=120.0,
            )
        except Exception as e:
            raise LLMError(f"话题分段 LLM 调用失败: {e}") from e

        try:
            topics = self._parse_response(response)
        except Exception as e:
            raise LLMError(f"话题分段结果解析失败: {e}") from e

        logger.info(f"话题分段完成: {len(topics)} 个话题")
        return topics

    def _format_transcript(self, transcript: TranscriptResult) -> str:
        """格式化转录文本（带时间戳）"""
        lines: list[str] = []
        for seg in transcript.segments:
            lines.append(f"[{seg.start:.1f}s-{seg.end:.1f}s] {seg.text}")
        return "\n".join(lines)

    def _parse_response(self, response: str) -> list[TopicSegment]:
        """解析 LLM JSON 响应"""
        # 提取 JSON 部分（可能包含 markdown 代码块）
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        data = json.loads(json_str)

        if not isinstance(data, list):
            raise ValueError(f"期望 JSON 数组，得到 {type(data).__name__}")

        topics: list[TopicSegment] = []
        for item in data:
            topics.append(
                TopicSegment(
                    start=float(item["start"]),
                    end=float(item["end"]),
                    topic=str(item["topic"]),
                    summary=str(item.get("summary", "")),
                )
            )

        return topics
