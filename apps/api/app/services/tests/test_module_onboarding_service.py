import unittest
from datetime import date
from types import SimpleNamespace

from app.services.module_onboarding_service import (
    batch_missing_module_metadata_flags,
    build_onboarding_suggestion,
    build_worker_onboarding_audit_metadata,
    is_upload_business_type_unset,
)


def _document(**overrides):
    defaults = {
        "id": "doc-1",
        "title": "Hop dong mua sam",
        "status": "searchable",
        "document_type": "HĐ",
        "classification_confidence": 0.92,
        "document_number": "01/HĐ-2026",
        "document_symbol": "HĐ-VT",
        "issued_date": date(2026, 6, 7),
        "issuing_agency": "Phong Vat Tu",
        "excerpt": "Hop dong cung cap vat tu",
        "recipient": None,
        "metadata_source": "auto",
        "metadata_reviewed_at": None,
        "business_type": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class ModuleOnboardingServiceTests(unittest.TestCase):
    def test_contract_mapping_from_document_type(self) -> None:
        suggestion = build_onboarding_suggestion(_document(document_type="HĐ"))

        self.assertTrue(suggestion["eligible"])
        self.assertEqual(suggestion["target_module"], "contract")
        self.assertEqual(suggestion["suggested_business_type"], "contract")
        self.assertEqual(suggestion["suggested_module_fields"]["contract_number"], "01/HĐ-2026")
        self.assertEqual(suggestion["suggested_module_fields"]["sign_date"], "2026-06-07")

    def test_decision_mapping_qd(self) -> None:
        suggestion = build_onboarding_suggestion(
            _document(
                document_type="QĐ",
                document_number="01/QĐ-PVT",
                excerpt="Quy dinh quan ly vat tu",
            )
        )

        self.assertTrue(suggestion["eligible"])
        self.assertEqual(suggestion["target_module"], "decision")
        self.assertEqual(suggestion["module_kind"], "decision")
        self.assertEqual(suggestion["suggested_module_fields"]["decision_kind"], "decision")

    def test_dispatch_outgoing_from_vv_excerpt(self) -> None:
        suggestion = build_onboarding_suggestion(
            _document(
                document_type="CV",
                excerpt="V/v cung cap bao cao tien do",
                recipient="So Tai chinh",
            )
        )

        self.assertTrue(suggestion["eligible"])
        self.assertEqual(suggestion["target_module"], "dispatch")
        self.assertEqual(suggestion["suggested_business_type"], "outgoing_dispatch")
        self.assertEqual(suggestion["module_kind"], "outgoing")

    def test_dispatch_incoming_from_recipient(self) -> None:
        suggestion = build_onboarding_suggestion(
            _document(
                document_type="CV",
                excerpt="De nghi cap vat tu",
                recipient="Phong Vat Tu",
            )
        )

        self.assertTrue(suggestion["eligible"])
        self.assertEqual(suggestion["suggested_business_type"], "incoming_dispatch")
        self.assertEqual(suggestion["module_kind"], "incoming")

    def test_prioritizes_existing_business_type(self) -> None:
        suggestion = build_onboarding_suggestion(
            _document(
                document_type="CV",
                business_type="contract",
                excerpt="V/v test",
            )
        )

        self.assertTrue(suggestion["eligible"])
        self.assertEqual(suggestion["target_module"], "contract")
        self.assertEqual(suggestion["suggested_business_type"], "contract")
        self.assertIn("document_type=CV_differs_from_business_type", suggestion["reasons"])

    def test_blocks_when_not_searchable(self) -> None:
        suggestion = build_onboarding_suggestion(_document(status="processing"))

        self.assertFalse(suggestion["eligible"])
        self.assertEqual(suggestion["block_reason"], "not_searchable")

    def test_blocks_manual_metadata(self) -> None:
        suggestion = build_onboarding_suggestion(_document(metadata_source="manual"))

        self.assertFalse(suggestion["eligible"])
        self.assertEqual(suggestion["block_reason"], "manual_metadata")

    def test_blocks_unmapped_document_type(self) -> None:
        suggestion = build_onboarding_suggestion(_document(document_type="GM"))

        self.assertFalse(suggestion["eligible"])
        self.assertEqual(suggestion["block_reason"], "unmapped_document_type")

    def test_blocks_low_confidence_unknown(self) -> None:
        suggestion = build_onboarding_suggestion(
            _document(document_type="UNKNOWN", classification_confidence=0.40)
        )

        self.assertFalse(suggestion["eligible"])
        self.assertEqual(suggestion["block_reason"], "unmapped_document_type")
        self.assertTrue(suggestion["needs_metadata_review"])

    def test_worker_audit_skips_when_upload_business_type_set(self) -> None:
        document = _document(business_type="contract")
        self.assertFalse(is_upload_business_type_unset(document))
        self.assertIsNone(
            build_worker_onboarding_audit_metadata(
                document,
                upload_business_type_unset=False,
            )
        )

    def test_worker_audit_when_upload_business_type_unset(self) -> None:
        document = _document(status="chunking", document_type="HĐ")
        audit = build_worker_onboarding_audit_metadata(
            document,
            upload_business_type_unset=True,
        )
        self.assertIsNotNone(audit)
        self.assertFalse(audit["applied"])
        self.assertEqual(audit["target_module"], "contract")
        self.assertEqual(audit["suggested_business_type"], "contract")

    def test_worker_audit_ignores_searchable_requirement(self) -> None:
        suggestion = build_onboarding_suggestion(
            _document(status="chunking", document_type="QĐ"),
            require_searchable=False,
        )
        self.assertIsNone(suggestion["block_reason"])
        self.assertEqual(suggestion["target_module"], "decision")

    def test_batch_missing_module_metadata_flags(self) -> None:
        documents = [
            _document(id="doc-contract", business_type="contract"),
            _document(id="doc-dispatch", business_type="incoming_dispatch"),
            _document(id="doc-failed", status="failed", business_type="decision"),
            _document(id="doc-no-bt", business_type=None),
        ]

        class _FakeDb:
            def scalars(self, _stmt):
                return iter(["doc-contract"])

        flags = batch_missing_module_metadata_flags(_FakeDb(), documents)

        self.assertFalse(flags["doc-contract"])
        self.assertTrue(flags["doc-dispatch"])
        self.assertFalse(flags["doc-failed"])
        self.assertFalse(flags["doc-no-bt"])


if __name__ == "__main__":
    unittest.main()
