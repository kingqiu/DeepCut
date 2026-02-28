"""LLM 客户端封装：指数退避重试、超时、token 记录"""

import time
from typing import Literal

from loguru import logger
from openai import OpenAI

from deepcut.exceptions import LLMError, LLMRateLimitError, LLMTimeoutError


class LLMClient:
    """OpenAI 兼容 LLM 客户端

    所有 LLM 调用统一通过此客户端，pipeline 步骤不直接调用 OpenAI SDK。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        max_retries: int = 3,
        timeout: float = 300.0,
    ) -> None:
        if not api_key:
            raise LLMError("OPENAI_API_KEY 未设置")

        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: float | None = None,
    ) -> str:
        """发送 chat completion 请求

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数
            max_tokens: 最大输出 token 数
            timeout: 单次请求超时（覆盖默认值）

        Returns:
            LLM 回复文本

        Raises:
            LLMError: 调用失败
            LLMTimeoutError: 超时
            LLMRateLimitError: 速率限制
        """
        effective_timeout = timeout or self.timeout
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            start_time = time.monotonic()
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=effective_timeout,
                )

                elapsed = time.monotonic() - start_time
                content = response.choices[0].message.content or ""

                # 记录 token 消耗
                usage = response.usage
                if usage:
                    logger.info(
                        f"LLM 调用完成: model={self.model}, "
                        f"prompt_tokens={usage.prompt_tokens}, "
                        f"completion_tokens={usage.completion_tokens}, "
                        f"elapsed={elapsed:.1f}s"
                    )
                else:
                    logger.info(f"LLM 调用完成: elapsed={elapsed:.1f}s")

                return content

            except Exception as e:
                elapsed = time.monotonic() - start_time
                last_error = e
                error_type = type(e).__name__

                # 判断错误类型
                error_str = str(e).lower()
                if "rate_limit" in error_str or "429" in error_str:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"LLM 速率限制 (attempt {attempt}/{self.max_retries}), "
                        f"等待 {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                    continue
                elif "timeout" in error_str or "timed out" in error_str:
                    logger.warning(
                        f"LLM 超时 (attempt {attempt}/{self.max_retries}, "
                        f"{elapsed:.1f}s): {e}"
                    )
                    if attempt < self.max_retries:
                        time.sleep(1)
                        continue
                    raise LLMTimeoutError(
                        f"LLM 调用超时 ({self.max_retries} 次重试后): {e}"
                    ) from e
                else:
                    logger.error(
                        f"LLM 调用失败 (attempt {attempt}/{self.max_retries}): "
                        f"{error_type}: {e}"
                    )
                    if attempt < self.max_retries:
                        wait_time = 2 ** (attempt - 1)
                        time.sleep(wait_time)
                        continue

        raise LLMError(
            f"LLM 调用失败 ({self.max_retries} 次重试后): {last_error}"
        )

    def chat_with_images(
        self,
        system_prompt: str,
        text_prompt: str,
        image_base64_list: list[str],
        model_override: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: float | None = None,
    ) -> str:
        """发送包含图片的 chat completion 请求（多模态）

        Args:
            system_prompt: 系统提示词
            text_prompt: 文本提示词
            image_base64_list: base64 编码的 JPEG 图片列表
            model_override: 覆盖默认模型（如用 vision 模型）
            temperature: 温度参数
            max_tokens: 最大输出 token 数
            timeout: 单次请求超时

        Returns:
            LLM 回复文本
        """
        # 构建 content: text + images
        content: list[dict[str, str | dict[str, str]]] = [
            {"type": "text", "text": text_prompt},
        ]
        for img_b64 in image_base64_list:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}",
                },
            })

        effective_timeout = timeout or self.timeout
        effective_model = model_override or self.model
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            start_time = time.monotonic()
            try:
                response = self._client.chat.completions.create(
                    model=effective_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content},  # type: ignore[arg-type]
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=effective_timeout,
                )

                elapsed = time.monotonic() - start_time
                result = response.choices[0].message.content or ""

                usage = response.usage
                if usage:
                    logger.info(
                        f"VL 调用完成: model={effective_model}, "
                        f"prompt_tokens={usage.prompt_tokens}, "
                        f"completion_tokens={usage.completion_tokens}, "
                        f"images={len(image_base64_list)}, "
                        f"elapsed={elapsed:.1f}s"
                    )

                return result

            except Exception as e:
                elapsed = time.monotonic() - start_time
                last_error = e
                error_str = str(e).lower()

                if "rate_limit" in error_str or "429" in error_str:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"VL 速率限制 (attempt {attempt}/{self.max_retries}), "
                        f"等待 {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                    continue
                elif "timeout" in error_str or "timed out" in error_str:
                    logger.warning(
                        f"VL 超时 (attempt {attempt}/{self.max_retries}, "
                        f"{elapsed:.1f}s): {e}"
                    )
                    if attempt < self.max_retries:
                        time.sleep(1)
                        continue
                    raise LLMTimeoutError(
                        f"VL 调用超时 ({self.max_retries} 次重试后): {e}"
                    ) from e
                else:
                    logger.error(
                        f"VL 调用失败 (attempt {attempt}/{self.max_retries}): "
                        f"{type(e).__name__}: {e}"
                    )
                    if attempt < self.max_retries:
                        time.sleep(2 ** (attempt - 1))
                        continue

        raise LLMError(
            f"VL 调用失败 ({self.max_retries} 次重试后): {last_error}"
        )
