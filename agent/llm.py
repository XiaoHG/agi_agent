"""Real LLM client integration for DeepSeek-compatible chat models."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-pro"


class LLMError(Exception):
    """Raised when the real LLM provider cannot complete a request."""


@dataclass(frozen=True)
class LLMMessage:
    """One chat message sent to or returned from the LLM."""

    role: str  # 消息角色，例如 system、user、assistant
    content: str  # 消息正文

    def to_dict(self) -> dict[str, str]:
        """Convert the message to the OpenAI-compatible API shape."""

        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class LLMResponse:
    """Normalized response returned by the LLM provider."""

    model: str  # 实际请求使用的模型名
    content: str  # 模型最终回复
    raw: dict[str, Any] = field(repr=False)  # 原始响应，保留给调试和后续 trace 使用


@dataclass(frozen=True)
class DeepSeekConfig:
    """Runtime configuration for the DeepSeek chat API."""

    api_key: str  # DeepSeek API Key，只从环境变量读取，不写入仓库
    model: str = DEFAULT_DEEPSEEK_MODEL  # 默认使用 DeepSeek V4 Pro
    api_url: str = DEFAULT_DEEPSEEK_API_URL  # OpenAI-compatible chat completions endpoint
    temperature: float = 0.2  # 学习与代码解释场景优先稳定输出
    max_tokens: int = 1_000  # 控制单次回复长度，避免开发阶段输出过长
    timeout_seconds: int = 60  # 真实网络请求最大等待时间

    @classmethod
    def from_env(cls) -> "DeepSeekConfig":
        """Build config from environment variables."""

        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise LLMError("Missing DEEPSEEK_API_KEY environment variable.")

        return cls(
            api_key=api_key,
            model=os.environ.get("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL).strip() or DEFAULT_DEEPSEEK_MODEL,
            api_url=os.environ.get("DEEPSEEK_API_URL", DEFAULT_DEEPSEEK_API_URL).strip() or DEFAULT_DEEPSEEK_API_URL,
            temperature=float(os.environ.get("DEEPSEEK_TEMPERATURE", "0.2")),
            max_tokens=int(os.environ.get("DEEPSEEK_MAX_TOKENS", "1000")),
            timeout_seconds=int(os.environ.get("DEEPSEEK_TIMEOUT_SECONDS", "60")),
        )


class DeepSeekLLMClient:
    """Small real DeepSeek chat client using the OpenAI-compatible HTTP API."""

    def __init__(self, config: DeepSeekConfig | None = None) -> None:
        """Initialize the instance state needed by this object."""
        self.config = config or DeepSeekConfig.from_env()  # 默认从环境变量读取真实配置

    def chat(self, messages: list[LLMMessage]) -> LLMResponse:
        """Send messages to DeepSeek and return a normalized response."""

        if not messages:
            raise LLMError("At least one message is required.")

        payload = {
            "model": self.config.model,
            "messages": [message.to_dict() for message in messages],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        raw = self._post_json(payload)
        content = self._extract_content(raw)
        return LLMResponse(model=self.config.model, content=content, raw=raw)

    def complete(self, user_input: str, system_prompt: str | None = None) -> LLMResponse:
        """Run one real LLM turn with an optional system prompt."""

        messages: list[LLMMessage] = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role="user", content=user_input))
        return self.chat(messages)

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Post JSON to the DeepSeek API and return decoded JSON."""

        body = json.dumps(payload).encode("utf-8")
        request = Request(
            self.config.api_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as error:
            error_body = error.read().decode("utf-8", errors="replace")
            raise LLMError(f"DeepSeek API HTTP {error.code}: {error_body}") from error
        except URLError as error:
            raise LLMError(f"DeepSeek API network error: {error.reason}") from error

        try:
            decoded = json.loads(response_body)
        except json.JSONDecodeError as error:
            raise LLMError("DeepSeek API returned invalid JSON.") from error
        if not isinstance(decoded, dict):
            raise LLMError("DeepSeek API returned an unexpected response shape.")
        return decoded

    def _extract_content(self, raw: dict[str, Any]) -> str:
        """Extract assistant content from an OpenAI-compatible response."""

        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMError("DeepSeek API response does not contain choices.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LLMError("DeepSeek API response contains an invalid choice.")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise LLMError("DeepSeek API response does not contain a message.")

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMError("DeepSeek API response message is empty.")
        return content.strip()
