# Task Vừa Hoàn Thành: Module Chunking OCR Text Hành Chính Tiếng Việt

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã tạo module chunking OCR text mới tại `apps/api/app/services/ocr_chunking/` để phục vụ retrieval/RAG cho văn bản hành chính tiếng Việt. Module độc lập với `ChunkingService` cũ nên không thay đổi workflow OCR/indexing hiện tại.

Pipeline đã có:
- OCR text/layout.
- Normalize tiếng Việt nhẹ và sửa fuzzy lỗi OCR phổ biến.
- Detect `doc_type` theo thể thức văn bản, ưu tiên hình thức hơn nội dung.
- Map `doc_type` vào nhóm A/B/C/D/E.
- Chọn strategy chunking riêng theo nhóm.
- Tạo structural chunks.
- Tạo retrieval child chunks khi chunk quá dài.
- Gắn metadata, confidence, page/bbox, entities, flags table/signature/appendix.
- Fallback rõ ràng cho `UNKNOWN`, OCR lỗi hoặc mất bố cục.
- Trả JSON chuẩn qua `Chunk.to_dict()`.

## Kết Quả Chính

Files mới:
- `apps/api/app/services/ocr_chunking/mappings.py`: mapping nhãn văn bản sang nhóm A/B/C/D/E.
- `apps/api/app/services/ocr_chunking/anchors.py`: regex và anchor phrases.
- `apps/api/app/services/ocr_chunking/schemas.py`: `OCRDocument`, `OCRPage`, `OCRBlock`, `Chunk`.
- `apps/api/app/services/ocr_chunking/normalizer.py`: normalize tiếng Việt nhẹ, bỏ dấu cho detect anchor.
- `apps/api/app/services/ocr_chunking/classifier.py`: detect `doc_type` rule-based/local.
- `apps/api/app/services/ocr_chunking/entities.py`: extract entity cơ bản cho metadata retrieval.
- `apps/api/app/services/ocr_chunking/pipeline.py`: hàm chính `chunk_document(input: OCRDocument) -> list[Chunk]`.
- `apps/api/app/services/ocr_chunking/README.md`: hướng dẫn dùng module.
- `apps/api/app/services/ocr_chunking/tests/test_pipeline.py`: unit test 5 mẫu bắt buộc.

Ghi chú vận hành:
- `apps/api/tests` hiện thuộc `root`, nên test được đặt trong package module và chạy bằng `python3 -m unittest`.
- Module chưa thay worker cũ để tránh migrate DB/Qdrant payload trong cùng task.

## Đã Kiểm Tra

```bash
PYTHONPATH=apps/api python3 -m py_compile apps/api/app/services/ocr_chunking/*.py apps/api/app/services/ocr_chunking/tests/test_pipeline.py
PYTHONPATH=apps/api python3 -m unittest app.services.ocr_chunking.tests.test_pipeline
```

Kết quả:
- Compile pass.
- Unit test pass 5/5 cho `QĐ`, `KH`, `CV`, `HĐ`, `UNKNOWN OCR lỗi`.

## Task Tiếp Theo Đề Xuất

1. Tích hợp `ocr_chunking` vào worker:
   - Map output mới vào bảng `document_chunks` hiện có hoặc thêm cột metadata nếu cần.
   - Đưa `section_role`, `section_path`, `doc_group`, `confidence`, `fallback_info` vào Qdrant payload.
   - Giữ rollback path về `ChunkingService` cũ trong giai đoạn thử nghiệm.

2. Preview file inline trong detail:
   - Preview PDF/image/text cạnh OCR text và metadata.
   - Fallback download cho DOCX/XLSX.
