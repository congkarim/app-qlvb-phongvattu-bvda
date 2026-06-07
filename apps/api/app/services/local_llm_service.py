from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)

HEALTH_TIMEOUT_SECONDS = 5


class LocalLLMError(Exception):
    """Base error for local LLM client failures."""


class LocalLLMBackendDisabledError(LocalLLMError):
    """Raised when RAG generation backend is not ollama."""


class LocalLLMUnavailableError(LocalLLMError):
    """Raised when Ollama is unreachable or returns an error."""


class LocalLLMTimeoutError(LocalLLMUnavailableError):
    """Raised when Ollama does not respond in time."""


class LocalLLMResponseError(LocalLLMError):
    """Raised when Ollama returns an unexpected payload."""


@dataclass(frozen=True)
class GenerateResult:
    text: str
    model_name: str
    latency_ms: int


class LocalLLMService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def backend(self) -> str:
        return self.settings.rag_generation_backend.strip().lower()

    def is_generative_enabled(self) -> bool:
        return self.backend == "ollama"

    def is_available(self) -> bool:
        if not self.is_generative_enabled():
            return False
        try:
            self._get_json(f"{self._base_url()}/api/tags", timeout=HEALTH_TIMEOUT_SECONDS)
            return True
        except LocalLLMError as exc:
            logger.debug("Ollama health check failed: %s", exc)
            return False

    def generate(self, *, system: str, user: str) -> GenerateResult:
        if not self.is_generative_enabled():
            raise LocalLLMBackendDisabledError(
                f"Local LLM is disabled for backend={self.settings.rag_generation_backend!r}"
            )

        started = time.perf_counter()
        payload = {
            "model": self.settings.rag_llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": self.settings.rag_llm_temperature,
                "num_predict": self.settings.rag_llm_max_output_tokens,
            },
        }
        response = self._post_json(
            f"{self._base_url()}/api/chat",
            payload=payload,
            timeout=self.settings.rag_llm_timeout_seconds,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        message = response.get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LocalLLMResponseError("Ollama chat response missing assistant content")
        model_name = response.get("model") or self.settings.rag_llm_model
        if not isinstance(model_name, str):
            model_name = self.settings.rag_llm_model
        return GenerateResult(text=content.strip(), model_name=model_name, latency_ms=latency_ms)

    def _base_url(self) -> str:
        return self.settings.ollama_base_url.rstrip("/")

    def _get_json(self, url: str, *, timeout: float) -> dict[str, Any]:
        request = Request(url, headers={"Accept": "application/json"}, method="GET")
        return self._read_json(request, timeout=timeout)

    def _post_json(self, url: str, *, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            url,
            data=data,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        return self._read_json(request, timeout=timeout)

    def _read_json(self, request: Request, *, timeout: float) -> dict[str, Any]:
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LocalLLMUnavailableError(
                f"Ollama HTTP {exc.code}: {detail[:240]}"
            ) from exc
        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            if "timed out" in str(reason).lower():
                raise LocalLLMTimeoutError(f"Ollama request timed out after {timeout}s") from exc
            raise LocalLLMUnavailableError(f"Ollama request failed: {reason}") from exc

        if not body:
            return {}
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise LocalLLMResponseError("Ollama returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise LocalLLMResponseError("Ollama JSON response must be an object")
        return parsed
