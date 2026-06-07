import unittest
from unittest.mock import MagicMock, patch

from app.core.config import Settings
from app.services.ops_service import OpsService


class OpsServiceLLMStatusTests(unittest.TestCase):
    def test_extractive_backend_reports_ok_without_ollama(self) -> None:
        service = OpsService(db=MagicMock())
        service.settings = Settings(rag_generation_backend="extractive")

        status = service._get_llm_status()

        self.assertEqual(status.status, "ok")
        self.assertEqual(status.name, "extractive")
        self.assertFalse(status.details["reachable"])
        self.assertFalse(status.details["model_loaded"])

    @patch("app.services.ops_service.LocalLLMService")
    def test_ollama_unreachable_reports_unavailable(self, mock_llm_cls) -> None:
        mock_llm = mock_llm_cls.return_value
        mock_llm.is_available.return_value = False

        service = OpsService(db=MagicMock())
        service.settings = Settings(rag_generation_backend="ollama")

        status = service._get_llm_status()

        self.assertEqual(status.status, "unavailable")
        self.assertIn("not reachable", status.error or "")


if __name__ == "__main__":
    unittest.main()
