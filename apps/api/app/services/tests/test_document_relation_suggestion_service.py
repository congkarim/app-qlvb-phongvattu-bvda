import hashlib
import unittest
from types import SimpleNamespace
from uuid import uuid4

from app.utils.document_number import normalize_document_number
from app.services.document_relation_suggestion_service import (
    compute_suggestion_confidence,
    extract_reference_candidates,
    infer_relation_type_from_context,
    select_source_chunks,
)


def _chunk(**overrides):
    defaults = {
        "id": "chunk-1",
        "chunk_index": 0,
        "text": "",
        "page_from": 1,
        "page_to": 1,
        "section_role": "article",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class DocumentRelationSuggestionServiceTests(unittest.TestCase):
    def test_normalize_document_number_fixes_qd_symbol(self) -> None:
        self.assertEqual(normalize_document_number("01/QD-REL-abc"), "01/QĐ-REL-abc")

    def test_extract_reference_from_can_cu_quyet_dinh(self) -> None:
        text = "Căn cứ Quyết định số 01/QD-REL-abc của Giám đốc về việc quản lý vật tư."
        candidates = extract_reference_candidates(text)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].normalized_number, "01/QĐ-REL-abc")
        self.assertEqual(candidates[0].pattern_strength, "strong")

    def test_infer_relation_type_can_cu(self) -> None:
        relation_type, reason = infer_relation_type_from_context(
            "Căn cứ Quyết định số",
            "01/QĐ-REL-abc",
        )
        self.assertEqual(relation_type, "references")
        self.assertEqual(reason, "anchor:can_cu")

    def test_infer_relation_type_defaults_to_related(self) -> None:
        relation_type, reason = infer_relation_type_from_context("theo dõi số", "01/CV-REL-abc")
        self.assertEqual(relation_type, "related")
        self.assertIsNone(reason)

    def test_compute_confidence_high_for_can_cu_page_one(self) -> None:
        confidence, reasons, tier = compute_suggestion_confidence(
            pattern_strength="strong",
            anchor_reason="anchor:can_cu",
            chunk=_chunk(),
        )
        self.assertGreaterEqual(confidence, 0.80)
        self.assertEqual(tier, "high")
        self.assertIn("exact_document_number_match", reasons)
        self.assertIn("anchor:can_cu", reasons)

    def test_select_source_chunks_prefers_article_on_page_one(self) -> None:
        chunks = [
            _chunk(id="c0", chunk_index=0, section_role="article", text="Căn cứ Quyết định số 01/QD-A"),
            _chunk(id="c1", chunk_index=1, page_from=2, section_role="signature", text="Giám đốc"),
        ]
        selected = select_source_chunks(chunks)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].id, "c0")


class DocumentRelationSuggestionRepoIntegrationTests(unittest.TestCase):
    def test_cv_chunk_references_qd_document(self) -> None:
        try:
            from app.db.session import SessionLocal
            from app.repositories.document_repository import DocumentRepository
            from app.services.document_relation_suggestion_service import DocumentRelationSuggestionService
        except Exception as exc:  # pragma: no cover - optional when DB unavailable
            self.skipTest(f"Database unavailable: {exc}")
            return

        db = SessionLocal()
        suffix = uuid4().hex[:10]
        qd_number = f"01/QD-REL-{suffix}"
        documents = DocumentRepository(db)
        created_ids: list[str] = []
        try:
            target = documents.create_document(
                title=f"[TEST] Relation suggestion QD {suffix}",
                original_filename=f"rel-suggest-qd-{suffix}.txt",
                file_path=f"/tmp/rel-suggest-qd-{suffix}.txt",
                content_type="text/plain",
                document_type="QĐ",
                document_number=qd_number,
                business_type="decision",
            )
            source = documents.create_document(
                title=f"[TEST] Relation suggestion CV {suffix}",
                original_filename=f"rel-suggest-cv-{suffix}.txt",
                file_path=f"/tmp/rel-suggest-cv-{suffix}.txt",
                content_type="text/plain",
                document_type="CV",
                document_number=f"01/CV-REL-{suffix}",
                business_type="incoming_dispatch",
            )
            created_ids.extend([target.id, source.id])
            documents.update_status(target, "searchable")
            documents.update_status(source, "searchable")
            chunk_text = f"Căn cứ Quyết định số {qd_number} của Giám đốc về việc quản lý vật tư."
            documents.create_chunk(
                document_id=source.id,
                chunk_index=0,
                text=chunk_text,
                content_hash=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
                page_from=1,
                page_to=1,
                section_role="article",
            )
            db.commit()

            result = DocumentRelationSuggestionService(db).suggest_relations(source.id)
            self.assertEqual(result["candidate_count"], 1)
            suggestion = result["suggestions"][0]
            self.assertEqual(suggestion["target_document_id"], target.id)
            self.assertEqual(suggestion["relation_type"], "references")
            self.assertIn(suggestion["confidence_tier"], {"high", "review"})
        finally:
            for document_id in created_ids:
                document = documents.get_document(document_id)
                if document is not None:
                    from datetime import datetime, timezone

                    document.deleted_at = datetime.now(timezone.utc)
                    db.add(document)
            db.commit()
            db.close()


if __name__ == "__main__":
    unittest.main()
