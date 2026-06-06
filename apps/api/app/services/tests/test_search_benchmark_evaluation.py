import unittest

from app.scripts.benchmark_search_fixtures import _calculate_metrics, _evaluate_search_quality


class SearchBenchmarkEvaluationTests(unittest.TestCase):
    def test_calculate_metrics_for_top_rank_results(self) -> None:
        metrics = _calculate_metrics(
            [
                {"rank": 1},
                {"rank": 1},
                {"rank": 1},
            ]
        )

        self.assertEqual(metrics["hit_rate"], 1.0)
        self.assertEqual(metrics["mrr"], 1.0)
        self.assertEqual(metrics["mean_rank"], 1.0)
        self.assertEqual(metrics["top1_count"], 3)
        self.assertEqual(metrics["top1_rate"], 1.0)

    def test_evaluate_search_quality_requires_review_when_hits_drop(self) -> None:
        metrics = _calculate_metrics(
            [
                {"rank": 1},
                {"rank": None},
                {"rank": 3},
            ]
        )

        evaluation = _evaluate_search_quality(metrics)

        self.assertEqual(evaluation["status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
