import unittest

from app.core.config import Settings
from app.services.local_llm_service import GenerateResult
from app.services.rag_answer_service import RagAnswerService
from app.services.rag_citation_validator import CitationValidator
from app.services.rag_context_builder import RagContextBuilder


class FakeSearchBackend:
    def __init__(self, results: list[dict]) -> None:
        self.results = results

    def semantic_search(self, **_kwargs) -> list[dict]:
        return self.results


class FakeLLMBackend:
    def __init__(self, *, available: bool = True, text: str = "Theo [1], nghiệm thu vật tư cần biên bản nghiệm thu.") -> None:
        self.available = available
        self.text = text

    def is_generative_enabled(self) -> bool:
        return True

    def is_available(self) -> bool:
        return self.available

    def generate(self, *, system: str, user: str) -> GenerateResult:
        return GenerateResult(text=self.text, model_name="test-model", latency_ms=42)


class RagAnswerServiceTests(unittest.TestCase):
    def _sample_evidence(self) -> list[dict]:
        return [
            {
                "document_id": "doc-1",
                "chunk_id": "chunk-1",
                "score": 0.91,
                "text": "Điều 3. Nghiệm thu vật tư phải có biên bản nghiệm thu và chứng chỉ xuất xứ.",
                "title": "Quy định nghiệm thu",
                "document_number": "QD-09/VT",
                "page_from": 2,
                "page_to": 2,
                "section_role": "article",
                "section_path": ["Điều 3"],
            }
        ]

    def test_answer_returns_grounded_citations(self) -> None:
        service = RagAnswerService(search_backend=FakeSearchBackend(self._sample_evidence()))

        response = service.answer(
            query="nghiệm thu vật tư cần hồ sơ gì",
            limit=3,
            min_score=0.3,
            max_citations=2,
        )

        self.assertTrue(response["grounded"])
        self.assertIsNone(response["fallback_reason"])
        self.assertIn("Nghiệm thu vật tư", response["answer"])
        self.assertEqual(len(response["citations"]), 1)
        self.assertEqual(response["citations"][0]["chunk_id"], "chunk-1")
        self.assertEqual(response["generation_mode"], "extractive")

    def test_answer_falls_back_when_evidence_is_weak(self) -> None:
        service = RagAnswerService(
            search_backend=FakeSearchBackend(
                [
                    {
                        "document_id": "doc-2",
                        "chunk_id": "chunk-2",
                        "score": 0.9,
                        "text": "Nội dung về lịch họp giao ban định kỳ.",
                    }
                ]
            )
        )

        response = service.answer(
            query="nghiệm thu vật tư cần hồ sơ gì",
            limit=3,
            min_score=0.3,
            max_citations=2,
        )

        self.assertFalse(response["grounded"])
        self.assertEqual(response["fallback_reason"], "insufficient_evidence")
        self.assertEqual(response["citations"], [])
        self.assertEqual(response["generation_mode"], "extractive")

    def test_generative_mock_returns_generation_mode_generative(self) -> None:
        service = RagAnswerService(
            search_backend=FakeSearchBackend(self._sample_evidence()),
            llm_backend=FakeLLMBackend(),
            settings=Settings(rag_generation_backend="ollama"),
        )

        response = service.answer(
            query="nghiệm thu vật tư cần hồ sơ gì",
            limit=3,
            min_score=0.3,
            max_citations=2,
        )

        self.assertEqual(response["generation_mode"], "generative")
        self.assertEqual(response["model_name"], "test-model")
        self.assertEqual(response["latency_ms"], 42)
        self.assertTrue(response["grounded"])
        self.assertIsNone(response["fallback_reason"])
        self.assertEqual(response["citations"][0]["chunk_id"], "chunk-1")

    def test_llm_unavailable_falls_back_to_extractive(self) -> None:
        service = RagAnswerService(
            search_backend=FakeSearchBackend(self._sample_evidence()),
            llm_backend=FakeLLMBackend(available=False),
            settings=Settings(rag_generation_backend="ollama"),
        )

        response = service.answer(
            query="nghiệm thu vật tư cần hồ sơ gì",
            limit=3,
            min_score=0.3,
            max_citations=2,
        )

        self.assertEqual(response["generation_mode"], "extractive")
        self.assertEqual(response["fallback_reason"], "llm_unavailable")
        self.assertTrue(response["grounded"])
        self.assertIn("Dựa trên các đoạn đã truy xuất", response["answer"])


class RagContextBuilderTests(unittest.TestCase):
    def test_build_numbered_context(self) -> None:
        evidence = [
            {
                "chunk_id": "chunk-1",
                "title": "Quy định",
                "document_number": "01/QD",
                "page_from": 1,
                "page_to": 1,
                "section_path": ["Điều 1"],
                "text": "Nghiệm thu vật tư phải có biên bản.",
            }
        ]
        context, ordered = RagContextBuilder(max_context_chars=2000).build(
            "nghiệm thu",
            evidence,
            snippet_fn=lambda _query, text: text,
        )
        self.assertIn("[1] chunk_id=chunk-1", context)
        self.assertEqual(len(ordered), 1)


class CitationValidatorTests(unittest.TestCase):
    def test_validate_accepts_valid_markers(self) -> None:
        result = CitationValidator().validate("Theo [1] và [2] nghiệm thu vật tư.", 2)
        self.assertTrue(result.valid)
        self.assertEqual(result.marker_indices, (1, 2))

    def test_validate_rejects_out_of_range_marker(self) -> None:
        result = CitationValidator().validate("Theo [3] nghiệm thu.", 1)
        self.assertFalse(result.valid)


if __name__ == "__main__":
    unittest.main()
