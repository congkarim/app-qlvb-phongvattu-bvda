import unittest

from app.services.search_rerank_service import SearchRerankConfig, SearchRerankService, normalize_search_text


class SearchRerankServiceTests(unittest.TestCase):
    def test_normalize_vietnamese_text(self) -> None:
        self.assertEqual(normalize_search_text("Phạm vi điều chỉnh"), "pham vi dieu chinh")
        self.assertEqual(normalize_search_text("Đấu   thầu"), "dau thau")

    def test_keyword_score_uses_configured_phrases(self) -> None:
        rerank = SearchRerankService()
        score = rerank.keyword_score(
            "phạm vi điều chỉnh",
            "Điều 1. Phạm vi điều chỉnh của văn bản",
        )
        self.assertGreater(score, 0.0)

    def test_score_boosts_prefix_rule(self) -> None:
        rerank = SearchRerankService()
        score = rerank.score(
            "phạm vi điều chỉnh",
            "Điều 1. Phạm vi điều chỉnh",
            vector_score=0.5,
            keyword_score=0.2,
        )
        weaker_score = rerank.score(
            "phạm vi điều chỉnh",
            "Nội dung khác không liên quan",
            vector_score=0.5,
            keyword_score=0.2,
        )
        self.assertGreater(score, weaker_score)

    def test_config_can_disable_sample_phrase_rules(self) -> None:
        rerank = SearchRerankService(
            SearchRerankConfig(
                phrase_boosts=(),
                prefix_boosts=(),
                missing_phrase_penalties=(),
                keyword_phrase_candidates=(),
            )
        )
        score = rerank.score(
            "phạm vi điều chỉnh",
            "Điều 1. Phạm vi điều chỉnh",
            vector_score=0.5,
            keyword_score=0.2,
        )
        self.assertAlmostEqual(score, 0.5 + 0.2 + 0.05 * 3 + 0.12, places=6)

    def test_weak_match_detection(self) -> None:
        rerank = SearchRerankService()
        self.assertFalse(rerank.is_weak_match("quản lý hồ sơ pháp lý", "Quy định quản lý hồ sơ pháp lý"))
        self.assertTrue(rerank.is_weak_match("quản lý hồ sơ pháp lý", "Nội dung không liên quan"))


if __name__ == "__main__":
    unittest.main()
