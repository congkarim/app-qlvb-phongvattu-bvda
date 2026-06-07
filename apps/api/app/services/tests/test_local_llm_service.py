import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from app.core.config import Settings
from app.services.local_llm_service import (
    LocalLLMBackendDisabledError,
    LocalLLMService,
    LocalLLMTimeoutError,
    LocalLLMUnavailableError,
)


def _settings(**overrides: object) -> Settings:
    defaults = {
        "rag_generation_backend": "ollama",
        "ollama_base_url": "http://ollama:11434",
        "rag_llm_model": "qwen2.5:3b-instruct",
        "rag_llm_timeout_seconds": 30,
        "rag_llm_max_context_chars": 8000,
        "rag_llm_max_output_tokens": 512,
        "rag_llm_temperature": 0.1,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class LocalLLMServiceTests(unittest.TestCase):
    def test_extractive_backend_does_not_call_ollama(self) -> None:
        service = LocalLLMService(_settings(rag_generation_backend="extractive"))
        self.assertFalse(service.is_generative_enabled())
        self.assertFalse(service.is_available())
        with self.assertRaises(LocalLLMBackendDisabledError):
            service.generate(system="sys", user="usr")

    @patch("app.services.local_llm_service.urlopen")
    def test_is_available_true_when_tags_endpoint_ok(self, mock_urlopen) -> None:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(
            {"models": [{"name": "qwen2.5:3b-instruct"}]}
        ).encode("utf-8")
        service = LocalLLMService(_settings())
        self.assertTrue(service.is_available())
        mock_urlopen.assert_called_once()

    @patch("app.services.local_llm_service.urlopen")
    def test_is_available_false_on_connection_error(self, mock_urlopen) -> None:
        mock_urlopen.side_effect = URLError("connection refused")
        service = LocalLLMService(_settings())
        self.assertFalse(service.is_available())

    @patch("app.services.local_llm_service.urlopen")
    def test_generate_returns_assistant_content(self, mock_urlopen) -> None:
        chat_body = json.dumps(
            {
                "model": "qwen2.5:3b-instruct",
                "message": {"role": "assistant", "content": "Trả lời thử [1]."},
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value.read.return_value = chat_body
        service = LocalLLMService(_settings())
        result = service.generate(system="Bạn là trợ lý.", user="Câu hỏi test")
        self.assertEqual(result.text, "Trả lời thử [1].")
        self.assertEqual(result.model_name, "qwen2.5:3b-instruct")
        self.assertGreaterEqual(result.latency_ms, 0)
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("app.services.local_llm_service.urlopen")
    def test_generate_raises_timeout_error(self, mock_urlopen) -> None:
        mock_urlopen.side_effect = URLError("timed out")
        service = LocalLLMService(_settings())
        with self.assertRaises(LocalLLMTimeoutError):
            service.generate(system="sys", user="usr")

    @patch("app.services.local_llm_service.urlopen")
    def test_generate_raises_unavailable_on_http_error(self, mock_urlopen) -> None:
        mock_urlopen.side_effect = HTTPError(
            url="http://ollama:11434/api/chat",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=io.BytesIO(b"model not found"),
        )
        service = LocalLLMService(_settings())
        with self.assertRaises(LocalLLMUnavailableError):
            service.generate(system="sys", user="usr")


if __name__ == "__main__":
    unittest.main()
