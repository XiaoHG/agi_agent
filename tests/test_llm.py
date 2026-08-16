"""Tests for real LLM configuration and response parsing."""

import unittest

from agent.llm import DeepSeekConfig, DeepSeekLLMClient, LLMError, LLMMessage


class DeepSeekLLMTests(unittest.TestCase):
    """Verify DeepSeek LLM integration boundaries without calling the network."""

    def test_message_exports_openai_compatible_shape(self) -> None:
        """Verify that message exports openai compatible shape."""
        message = LLMMessage(role="user", content="Explain agents.")

        self.assertEqual(message.to_dict(), {"role": "user", "content": "Explain agents."})

    def test_extract_content_from_response(self) -> None:
        """Verify that extract content from response."""
        client = DeepSeekLLMClient(
            DeepSeekConfig(
                api_key="test-key",
                model="deepseek-v4-pro",
                api_url="https://example.com/chat/completions",
            )
        )

        content = client._extract_content({"choices": [{"message": {"content": "Agent reasoning works."}}]})

        self.assertEqual(content, "Agent reasoning works.")

    def test_extract_content_rejects_invalid_response(self) -> None:
        """Verify that extract content rejects invalid response."""
        client = DeepSeekLLMClient(
            DeepSeekConfig(
                api_key="test-key",
                model="deepseek-v4-pro",
                api_url="https://example.com/chat/completions",
            )
        )

        with self.assertRaises(LLMError):
            client._extract_content({"choices": []})


if __name__ == "__main__":
    unittest.main()
