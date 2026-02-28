"""AI 模块单元测试：LLMClient / TagGenerator / TopicSegmenter"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from deepcut.ai.llm_client import LLMClient
from deepcut.ai.tag_generator import TagGenerator
from deepcut.ai.topic_segmenter import TopicSegmenter
from deepcut.exceptions import LLMError
from deepcut.models.analysis import TranscriptResult, TranscriptSegment
from deepcut.models.clip import ClipTags


# ---- LLMClient ----


class TestLLMClient:
    def test_init_requires_api_key(self) -> None:
        with pytest.raises(LLMError, match="OPENAI_API_KEY"):
            LLMClient(api_key="")

    def test_init_stores_params(self) -> None:
        client = LLMClient(api_key="sk-test", model="test-model", max_retries=5)
        assert client.model == "test-model"
        assert client.max_retries == 5

    @patch("deepcut.ai.llm_client.OpenAI")
    def test_chat_returns_content(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 5

        mock_choice = MagicMock()
        mock_choice.message.content = "hello world"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client.chat.completions.create.return_value = mock_response

        client = LLMClient(api_key="sk-test")
        result = client.chat(
            system_prompt="sys",
            user_prompt="user",
        )
        assert result == "hello world"
        mock_client.chat.completions.create.assert_called_once()

    @patch("deepcut.ai.llm_client.OpenAI")
    def test_chat_with_images_returns_content(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50

        mock_choice = MagicMock()
        mock_choice.message.content = "image analysis"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client.chat.completions.create.return_value = mock_response

        client = LLMClient(api_key="sk-test")
        result = client.chat_with_images(
            system_prompt="sys",
            text_prompt="analyze",
            image_base64_list=["abc123"],
            model_override="vl-model",
        )
        assert result == "image analysis"

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "vl-model"


# ---- TagGenerator ----


class TestTagGenerator:
    def _make_mock_llm(self) -> MagicMock:
        return MagicMock(spec=LLMClient)

    def _sample_clips_info(self) -> list[dict[str, str | float]]:
        return [
            {"start": 0.0, "end": 10.0, "split_reason": "scene", "transcript": "",
             "motion_types": "pan", "orientation": "landscape"},
            {"start": 10.0, "end": 25.0, "split_reason": "scene", "transcript": "hello",
             "motion_types": "static", "orientation": "landscape"},
        ]

    def test_empty_clips_returns_empty(self) -> None:
        llm = self._make_mock_llm()
        gen = TagGenerator(llm)
        assert gen.generate_batch([]) == []

    def test_generate_batch_text_mode(self) -> None:
        llm = self._make_mock_llm()
        llm.chat.return_value = json.dumps([
            {
                "clip_index": 0,
                "content": ["风景"],
                "scene": ["户外"],
                "object": ["树木"],
                "action": ["静止"],
                "emotion": ["宁静"],
                "technical": ["固定镜头"],
                "purpose": ["氛围感"],
            },
            {
                "clip_index": 1,
                "content": ["对话"],
                "scene": ["室内"],
                "object": ["人物"],
                "action": ["交谈"],
                "emotion": ["愉快"],
                "technical": ["中景"],
                "purpose": ["Vlog"],
            },
        ])

        gen = TagGenerator(llm)
        result = gen.generate_batch(self._sample_clips_info(), video_path=None)

        assert len(result) == 2
        assert isinstance(result[0], ClipTags)
        assert result[0].get_dimension("content") == ["风景"]
        assert result[1].get_dimension("scene") == ["室内"]
        llm.chat.assert_called_once()

    def test_generate_batch_llm_failure_returns_defaults(self) -> None:
        llm = self._make_mock_llm()
        llm.chat.side_effect = LLMError("timeout")

        gen = TagGenerator(llm)
        result = gen.generate_batch(self._sample_clips_info(), video_path=None)

        assert len(result) == 2
        for tags in result:
            assert tags.get_dimension("content") == ["未分类"]

    def test_parse_markdown_wrapped_json(self) -> None:
        llm = self._make_mock_llm()
        llm.chat.return_value = '```json\n[{"clip_index":0,"content":["美食"],"emotion":["满足"]}]\n```'

        gen = TagGenerator(llm)
        result = gen.generate_batch(
            [{"start": 0.0, "end": 10.0, "split_reason": "s", "transcript": "",
              "motion_types": "", "orientation": "landscape"}],
            video_path=None,
        )

        assert len(result) == 1
        assert result[0].get_dimension("content") == ["美食"]

    def test_build_clips_text_with_topic(self) -> None:
        llm = self._make_mock_llm()
        gen = TagGenerator(llm)
        text = gen._build_clips_text(
            [{"start": 0.0, "end": 30.0, "topic": "开场介绍", "summary": "视频开头",
              "orientation": "landscape"}],
            has_images=False,
        )
        assert "开场介绍" in text
        assert "视频开头" in text

    def test_build_clips_text_with_images(self) -> None:
        llm = self._make_mock_llm()
        gen = TagGenerator(llm)
        text = gen._build_clips_text(
            [{"start": 0.0, "end": 10.0, "orientation": "landscape"}],
            has_images=True,
        )
        assert "关键帧" in text
        assert "第 1 张图片" in text

    def test_default_tags(self) -> None:
        llm = self._make_mock_llm()
        gen = TagGenerator(llm)
        defaults = gen._default_tags()
        assert defaults.get_dimension("content") == ["未分类"]


# ---- TopicSegmenter ----


class TestTopicSegmenter:
    def _make_transcript(self) -> TranscriptResult:
        return TranscriptResult(
            language="zh",
            segments=[
                TranscriptSegment(start=0.0, end=10.0, text="今天我们来探店"),
                TranscriptSegment(start=10.5, end=20.0, text="这家店的装修非常好"),
                TranscriptSegment(start=20.5, end=30.0, text="菜品味道也不错"),
                TranscriptSegment(start=30.5, end=40.0, text="总结一下今天的体验"),
            ],
        )

    def test_empty_transcript_returns_empty(self) -> None:
        llm = MagicMock(spec=LLMClient)
        segmenter = TopicSegmenter(llm)
        transcript = TranscriptResult(language="zh", segments=[])
        assert segmenter.segment(transcript) == []

    def test_segment_parses_llm_response(self) -> None:
        llm = MagicMock(spec=LLMClient)
        llm.chat.return_value = json.dumps([
            {"start": 0.0, "end": 20.0, "topic": "探店介绍", "summary": "进店看环境"},
            {"start": 20.0, "end": 40.0, "topic": "菜品评价", "summary": "品尝和总结"},
        ])

        segmenter = TopicSegmenter(llm)
        topics = segmenter.segment(self._make_transcript())

        assert len(topics) == 2
        assert topics[0].topic == "探店介绍"
        assert topics[1].start == 20.0

    def test_segment_llm_failure_raises(self) -> None:
        llm = MagicMock(spec=LLMClient)
        llm.chat.side_effect = Exception("connection error")

        segmenter = TopicSegmenter(llm)
        with pytest.raises(LLMError):
            segmenter.segment(self._make_transcript())

    def test_segment_invalid_json_raises(self) -> None:
        llm = MagicMock(spec=LLMClient)
        llm.chat.return_value = "this is not json"

        segmenter = TopicSegmenter(llm)
        with pytest.raises(LLMError, match="解析失败"):
            segmenter.segment(self._make_transcript())

    def test_format_transcript(self) -> None:
        llm = MagicMock(spec=LLMClient)
        segmenter = TopicSegmenter(llm)
        text = segmenter._format_transcript(self._make_transcript())
        assert "[0.0s-10.0s]" in text
        assert "今天我们来探店" in text

    def test_parse_markdown_wrapped_response(self) -> None:
        llm = MagicMock(spec=LLMClient)
        llm.chat.return_value = '```json\n[{"start":0,"end":20,"topic":"话题A","summary":"摘要A"}]\n```'

        segmenter = TopicSegmenter(llm)
        topics = segmenter.segment(self._make_transcript())
        assert len(topics) == 1
        assert topics[0].topic == "话题A"
