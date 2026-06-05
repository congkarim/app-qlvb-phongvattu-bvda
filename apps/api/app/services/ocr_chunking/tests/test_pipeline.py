import unittest

from app.services.ocr_chunking import OCRDocument, OCRPage, chunk_document
from app.services.ocr_chunking.adapter import create_chunk_payloads


class OCRChunkingTests(unittest.TestCase):
    def test_group_a_decision_splits_by_article(self) -> None:
        document = OCRDocument(
            doc_id="doc-qd-1",
            pages=[
                OCRPage(
                    page_number=1,
                    confidence=0.92,
                    text=(
                        "ỦY BAN NHÂN DÂN\n"
                        "Số: 01/QĐ-UBND\n"
                        "QUYẾT ĐỊNH\n"
                        "Căn cứ Luật Tổ chức chính quyền địa phương;\n"
                        "Xét đề nghị của Phòng Vật tư;\n"
                        "Điều 1. Ban hành quy định quản lý vật tư.\n"
                        "1. Các đơn vị thực hiện kiểm kê định kỳ.\n"
                        "Điều 2. Tổ chức thực hiện.\n"
                        "Nơi nhận: Như Điều 2;\n"
                        "GIÁM ĐỐC\n"
                    ),
                )
            ],
            layout_confidence=0.9,
        )

        chunks = chunk_document(document)

        self.assertTrue(all(chunk.doc_type == "QĐ" for chunk in chunks))
        self.assertTrue(all(chunk.doc_group == "A" for chunk in chunks))
        self.assertTrue(any(chunk.section_role == "article" and chunk.article_number == "2" for chunk in chunks))
        self.assertTrue(any(chunk.section_role == "signature" for chunk in chunks))
        self.assert_json_schema(chunks[0].to_dict())

    def test_group_b_plan_splits_roman_sections_and_tasks(self) -> None:
        document = OCRDocument(
            doc_id="doc-kh-1",
            pages=[
                OCRPage(
                    page_number=1,
                    confidence=0.88,
                    text=(
                        "KẾ HOẠCH\n"
                        "Thực hiện mua sắm vật tư năm 2026\n"
                        "I. Mục đích\n"
                        "Bảo đảm vật tư cho sản xuất.\n"
                        "II. Nhiệm vụ\n"
                        "1. Phòng Vật tư lập danh mục nhu cầu.\n"
                        "2. Các đơn vị gửi báo cáo trước ngày 10/06/2026.\n"
                        "III. Tiến độ\n"
                        "Hoàn thành trong quý III.\n"
                    ),
                )
            ],
            layout_confidence=0.84,
        )

        chunks = chunk_document(document)

        self.assertEqual({chunk.doc_group for chunk in chunks}, {"B"})
        self.assertTrue(any(chunk.section_role == "task" for chunk in chunks))
        self.assertTrue(any("II. Nhiệm vụ" in chunk.section_title for chunk in chunks))

    def test_group_b_dispatch_detects_recipient_and_subject(self) -> None:
        document = OCRDocument(
            doc_id="doc-cv-1",
            text=(
                "CÔNG VĂN\n"
                "Số: 10/CV-VT\n"
                "V/v cung cấp số liệu tồn kho\n"
                "Kính gửi: Các đơn vị trực thuộc\n"
                "Thực hiện kế hoạch kiểm kê, đề nghị gửi số liệu trước ngày 15/06/2026.\n"
                "Nơi nhận: Như trên.\n"
            ),
            ocr_confidence=0.91,
            layout_confidence=0.8,
        )

        chunks = chunk_document(document)

        self.assertEqual(chunks[0].doc_type, "CV")
        self.assertEqual(chunks[0].doc_group, "B")
        self.assertTrue(any(chunk.section_role == "recipient" for chunk in chunks))
        self.assertTrue(any(chunk.entities.recipient == ["Các đơn vị trực thuộc"] for chunk in chunks))

    def test_group_c_contract_splits_by_article(self) -> None:
        document = OCRDocument(
            doc_id="doc-hd-1",
            text=(
                "HỢP ĐỒNG MUA BÁN VẬT TƯ\n"
                "Hôm nay, ngày 04 tháng 06 năm 2026\n"
                "Bên A: Công ty A\n"
                "Bên B: Công ty B\n"
                "Điều 1. Nội dung hợp đồng\n"
                "1. Bên B cung cấp vật tư theo phụ lục.\n"
                "Điều 2. Thanh toán\n"
                "Giá trị hợp đồng là 10.000.000 đồng.\n"
                "ĐẠI DIỆN BÊN A\n"
            ),
            ocr_confidence=0.9,
            layout_confidence=0.86,
        )

        chunks = chunk_document(document)

        self.assertEqual({chunk.doc_group for chunk in chunks}, {"C"})
        self.assertTrue(any(chunk.section_role == "article" and chunk.article_number == "2" for chunk in chunks))
        self.assertTrue(any(chunk.entities.amount == "10.000.000 đồng" for chunk in chunks))
        self.assertFalse(any(chunk.section_role == "appendix" for chunk in chunks))

    def test_group_a_detects_appendix_after_signature(self) -> None:
        document = OCRDocument(
            doc_id="doc-qd-appendix-1",
            pages=[
                OCRPage(
                    page_number=1,
                    confidence=0.91,
                    text=(
                        "ỦY BAN NHÂN DÂN\n"
                        "Số: 02/QĐ-UBND\n"
                        "QUYẾT ĐỊNH\n"
                        "Điều 1. Ban hành danh mục vật tư.\n"
                        "Điều 2. Tổ chức thực hiện.\n"
                        "Nơi nhận: Như Điều 2;\n"
                        "GIÁM ĐỐC\n"
                    ),
                ),
                OCRPage(
                    page_number=2,
                    confidence=0.9,
                    text=(
                        "PHỤ LỤC I\n"
                        "DANH MỤC VẬT TƯ BAN HÀNH KÈM THEO QUYẾT ĐỊNH SỐ 02/QĐ-UBND\n"
                        "STT   Tên vật tư   Số lượng\n"
                        "1     Thép tấm     20\n"
                    ),
                ),
            ],
            layout_confidence=0.86,
        )

        chunks = chunk_document(document)
        appendix_chunks = [chunk for chunk in chunks if chunk.section_role == "appendix"]

        self.assertTrue(appendix_chunks)
        self.assertTrue(all(chunk.contains_appendix for chunk in appendix_chunks))
        self.assertTrue(any(chunk.section_path[0] == "PHỤ LỤC I" for chunk in appendix_chunks))
        self.assertTrue(any(chunk.contains_table for chunk in appendix_chunks))
        self.assertFalse(any(chunk.requires_review for chunk in appendix_chunks))

    def test_group_a_detects_multiple_appendices_and_child_context(self) -> None:
        document = OCRDocument(
            doc_id="doc-qd-appendix-2",
            pages=[
                OCRPage(
                    page_number=1,
                    confidence=0.89,
                    text=(
                        "QUYẾT ĐỊNH\n"
                        "Điều 1. Ban hành kèm theo Quyết định này các phụ lục.\n"
                        "Điều 2. Tổ chức thực hiện.\n"
                        "PHỤ LỤC I\n"
                        "Danh mục thiết bị\n"
                        "Điều 1. Danh mục áp dụng.\n"
                        "1. Máy bơm nước.\n"
                        "PHỤ LỤC II\n"
                        "Danh mục vật tư\n"
                        "Điều 1. Danh mục áp dụng.\n"
                        "1. Ống thép.\n"
                    ),
                )
            ],
            layout_confidence=0.88,
        )

        chunks = chunk_document(document)
        appendix_paths = [chunk.section_path for chunk in chunks if chunk.contains_appendix]

        self.assertFalse(
            any(
                chunk.section_role == "appendix" and chunk.section_title.startswith("Điều 1. Ban hành")
                for chunk in chunks
            )
        )
        self.assertTrue(any(path[0] == "PHỤ LỤC I" for path in appendix_paths))
        self.assertTrue(any(path[0] == "PHỤ LỤC II" for path in appendix_paths))
        self.assertTrue(any(path[:2] == ["PHỤ LỤC I", "Điều 1"] for path in appendix_paths))
        self.assertTrue(any(path[:2] == ["PHỤ LỤC II", "Điều 1"] for path in appendix_paths))

    def test_body_mention_of_appendix_is_not_appendix_section(self) -> None:
        document = OCRDocument(
            doc_id="doc-no-appendix-false-positive",
            text=(
                "HỢP ĐỒNG MUA BÁN VẬT TƯ\n"
                "Bên A: Công ty A\n"
                "Bên B: Công ty B\n"
                "Điều 1. Nội dung hợp đồng\n"
                "1. Bên B cung cấp vật tư theo phụ lục do hai bên thống nhất.\n"
                "Điều 2. Thanh toán\n"
                "Giá trị hợp đồng là 10.000.000 đồng.\n"
                "ĐẠI DIỆN BÊN A\n"
            ),
            ocr_confidence=0.9,
            layout_confidence=0.86,
        )

        chunks = chunk_document(document)

        self.assertFalse(any(chunk.section_role == "appendix" for chunk in chunks))
        self.assertFalse(any(chunk.contains_appendix for chunk in chunks))

    def test_weak_appendix_heading_requires_review(self) -> None:
        document = OCRDocument(
            doc_id="doc-weak-appendix",
            pages=[
                OCRPage(
                    page_number=1,
                    confidence=0.58,
                    text=(
                        "CÔNG VĂN\n"
                        "Kính gửi: Các đơn vị\n"
                        "Nội dung triển khai kiểm kê vật tư.\n"
                        "PHU LUC\n"
                        "Danh sach kem theo cong van so 10/CV-VT\n"
                        "STT   Noi dung   So luong\n"
                    ),
                )
            ],
            layout_confidence=0.55,
        )

        chunks = chunk_document(document)
        appendix_chunks = [chunk for chunk in chunks if chunk.section_role == "appendix"]

        self.assertTrue(appendix_chunks)
        self.assertTrue(any(chunk.requires_review for chunk in appendix_chunks))

    def test_unknown_bad_ocr_uses_fallback_and_review(self) -> None:
        document = OCRDocument(
            doc_id="doc-unknown-1",
            pages=[
                OCRPage(page_number=1, confidence=0.42, text="Qyet dlnh ???\nNoi nhan ...\nabc   def   ghi"),
                OCRPage(page_number=2, confidence=0.4, text="Bang vo STT   Noi dung   Slg\nx x x"),
            ],
            layout_confidence=0.25,
        )

        chunks = chunk_document(document)

        self.assertEqual({chunk.doc_type for chunk in chunks}, {"UNKNOWN"})
        self.assertEqual({chunk.doc_group for chunk in chunks}, {"E"})
        self.assertTrue(all(chunk.fallback_info.used_fallback for chunk in chunks))
        self.assertTrue(any(chunk.requires_review for chunk in chunks))
        self.assertTrue(any(chunk.contains_table for chunk in chunks))

    def test_adapter_returns_db_payload_with_qdrant_metadata(self) -> None:
        page = OCRPage(
            page_number=1,
            confidence=0.9,
            text=(
                "QUYẾT ĐỊNH\n"
                "Căn cứ quy chế quản lý vật tư;\n"
                "Điều 1. Phạm vi áp dụng.\n"
                "Điều 2. Tổ chức thực hiện.\n"
            ),
        )

        payloads = create_chunk_payloads(doc_id="doc-adapter-1", document_type="QĐ", page_contents=[page])

        self.assertTrue(payloads)
        first = payloads[0]
        self.assertIn("content_hash", first)
        self.assertIn("chunk_metadata", first)
        self.assertEqual(first["page_from"], 1)
        self.assertEqual(first["page_to"], 1)
        self.assertEqual(first["chunk_metadata"]["doc_group"], "A")
        self.assertIn("section_role", first["chunk_metadata"])

    def assert_json_schema(self, payload: dict) -> None:
        expected_keys = {
            "chunk_id",
            "doc_id",
            "doc_type",
            "doc_group",
            "chunk_level",
            "section_role",
            "section_title",
            "section_path",
            "article_number",
            "clause_number",
            "point_number",
            "page_start",
            "page_end",
            "bbox_start",
            "bbox_end",
            "text",
            "text_normalized",
            "source_anchor",
            "confidence",
            "ocr_confidence",
            "layout_confidence",
            "classification_confidence",
            "parent_chunk_id",
            "previous_chunk_id",
            "next_chunk_id",
            "contains_table",
            "contains_signature",
            "contains_appendix",
            "requires_review",
            "entities",
            "fallback_info",
        }
        self.assertEqual(set(payload.keys()), expected_keys)
        self.assertIn("document_number", payload["entities"])
        self.assertIn("used_fallback", payload["fallback_info"])


if __name__ == "__main__":
    unittest.main()
