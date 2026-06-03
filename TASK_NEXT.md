# Task Tiếp Theo: Reprocess Công Văn Cũ Và Tối Ưu Keyword Index

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-03

## Task Vừa Hoàn Thành

Đã cải thiện OCR công văn có header hai bên/dấu mộc và bổ sung hybrid search PostgreSQL keyword + Qdrant vector.

Kết quả chính:
- VietOCR line ordering xử lý layout công văn có header hai bên nhưng thân văn bản một cột:
  - Header trái được gom theo cột trước.
  - Header phải được gom theo cột sau.
  - Thân văn bản tiếp tục đọc theo thứ tự trên xuống, trái sang phải.
- OCR postprocess nối lại các dòng công văn bị tách:
  - Tiêu ngữ `CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM`.
  - Header `ỦY BAN NHÂN DÂN XÃ MINH PHÚ`.
  - Ngày tháng `Minh Phú, ngày 27 tháng 5 năm 2026`.
  - Các câu nội dung bị tách dòng.
- Thêm cleanup cho nhiễu công văn:
  - `000001`, `CHUNICH`.
  - `số điện thoai` -> `số điện thoại`.
  - `MINH PHỦ` -> `MINH PHÚ`.
- OCR auto scoring ưu tiên marker quan trọng:
  - `Số:`
  - `Kính gửi`
  - `Người liên hệ`
  - `Điều`
  - `Khoản`
  - Tiêu ngữ quốc hiệu.
- Search API chuyển sang hybrid retrieval:
  - Qdrant vector candidates.
  - PostgreSQL keyword candidates trên `document_chunks.text`.
  - Rerank/dedup chung trong service.
- Search router truyền DB session vào service, giữ kiến trúc `router -> service -> repository`.
- Search response `score` hiển thị hybrid rerank score nên thứ tự và điểm nhất quán hơn.

Đã kiểm tra:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/services/document_content_service.py /app/app/services/ocr/paddle_vietocr_engine.py /app/app/services/search_service.py /app/app/repositories/document_repository.py /app/app/routers/search.py
docker compose run --rm --no-deps worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_007.png --engine paddle_vietocr --preprocess-mode raw clahe threshold --format json
docker compose run --rm --no-deps worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --files sample_007.png --engine paddle_vietocr --preprocess-mode auto --format json
docker compose up -d --build api
curl -fsS http://localhost:8000/health
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":3}'
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Nghị định 192 2026 chế độ phụ cấp đặc thù lĩnh vực y tế","limit":3}'
```

Kết quả benchmark `sample_007.png`:
- Trước tối ưu `raw`: CER `0.4241`, WER `0.4907`, accent loss `0.0`, confidence `0.9228`.
- Sau tối ưu `raw`: CER `0.2342`, WER `0.2963`, accent loss `0.0`, confidence `0.9266`.
- Sau tối ưu `auto`: CER `0.2658`, WER `0.2963`, accent loss `0.0`, confidence `0.9252`; giữ được `Người liên hệ: Nguyễn Văn An, số điện thoại 0900`.

Kết quả search:
- Query `Luật Đấu thầu phạm vi điều chỉnh` vẫn trả chunk `Điều 1. Phạm vi điều chính` top 1.
- Query `Nghị định 192 2026 chế độ phụ cấp đặc thù lĩnh vực y tế` vẫn trả đúng `Điều 1` của nghị định 192 top 1.

## Mục Tiêu Task Tiếp Theo

Reprocess các tài liệu công văn đã OCR bằng code cũ để tận dụng cleanup mới, sau đó tối ưu keyword search bằng index phù hợp nếu dữ liệu lớn hơn.

## Ràng Buộc Không Đổi

- Không dùng cloud OCR.
- Không dùng API LLM để sửa nội dung pháp lý.
- Docker Compose first.
- MVP first.
- Backend giữ `router -> service -> repository`.
- OCR pipeline local/on-prem.
- Không commit model files hoặc runtime artifacts.

## Phạm Vi Đề Xuất

### 1. Reprocess Công Văn Đã Upload

Vấn đề:
- Các document đã OCR trước task này vẫn giữ text/chunk cũ trong PostgreSQL và Qdrant.
- Search hành chính có thể vẫn trả nội dung cũ nếu chưa reprocess/reindex document.

Hướng xử lý:
- Thêm hoặc dùng script reprocess theo `document_id`.
- Xóa mềm hoặc thay thế page/chunk cũ của document mục tiêu theo transaction.
- OCR lại bằng code mới.
- Upsert lại Qdrant payload/vector cho chunks mới.
- Kiểm tra công văn JPEG cũ có cải thiện `Số:`, ngày tháng, `Kính gửi`, nhiễu đầu dòng.

### 2. Tối Ưu Keyword Search

Vấn đề:
- Hybrid keyword hiện dùng `ILIKE` theo term, phù hợp MVP nhưng chưa tối ưu cho tập dữ liệu lớn.

Hướng xử lý:
- Đánh giá `EXPLAIN ANALYZE` cho truy vấn keyword trên `document_chunks.text`.
- Nếu cần, thêm PostgreSQL `pg_trgm` hoặc full-text search tiếng Việt không dấu ở migration mới.
- Giữ API response hiện tại.

## Tiêu Chí Hoàn Thành

- Reprocess được ít nhất một công văn cũ và search trả text đã cleanup mới.
- Qdrant payload/chunks của document reprocess có `content_hash` mới và search vẫn mở đúng source.
- Keyword search có kế hoạch index rõ ràng hoặc migration nếu đã đủ cần thiết.
- Không phát sinh model/runtime artifact trong git.
