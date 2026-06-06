import unittest

from app.services.rag_answer_service import RagAnswerService


class FakeSearchBackend:
    def __init__(self, results: list[dict]) -> None:
        self.results = results

    def semantic_search(self, **_kwargs) -> list[dict]:
        return self.results


class RagAnswerServiceTests(unittest.TestCase):
    def test_answer_returns_grounded_citations(self) -> None:
        service = RagAnswerService(
            search_backend=FakeSearchBackend(
                [
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
            )
        )

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


if __name__ == "__main__":
    unittest.main()
