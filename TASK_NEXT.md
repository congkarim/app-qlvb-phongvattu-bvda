# Task Tiếp Theo: Dedup Và Hybrid Search Cho Văn Bản Trùng Nội Dung

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-01

## Task Vừa Hoàn Thành

Đã hoàn thành task cải thiện OCR scan tiếng Việt có dấu.

Kết quả chính:
- Nâng PaddleOCR từ `2.9.1` lên `3.3.0` và PaddlePaddle từ `2.6.2` lên `3.2.0`.
- Pin `numpy==1.26.4` để tránh lỗi/cảnh báo ABI với Torch/Paddle stack.
- Thêm cấu hình OCR qua env:
  - `OCR_ENGINE`
  - `OCR_LANG`
  - `OCR_USE_GPU`
  - `OCR_DEVICE`
  - `OCR_MODEL_DIR`
  - `OCR_PREPROCESS_MODE`
  - `OCR_MIN_CONFIDENCE`
  - `OCR_RESTORE_VIETNAMESE_TERMS`
- Giữ nguyên luồng PDF text-native bằng `pypdfium2`, chỉ OCR page scan hoặc ảnh.
- Thêm preprocess `auto`: raw resize, CLAHE và adaptive threshold.
- Hỗ trợ PaddleOCR 3.x `.predict(...)` và fallback PaddleOCR 2.x `.ocr(...)`.
- Thêm local OCR model path strategy: nếu có model tại `/models/ocr`, service truyền trực tiếp path vào PaddleOCR.
- Thêm hậu xử lý cục bộ cho các cụm pháp lý/tiêu ngữ tiếng Việt thường bị recognizer Latin làm rơi dấu.
- Cập nhật README và PROJECT_STATUS.

Benchmark mẫu sau sửa:

```text
confidence=0.9671
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
Điều 1. Phạm vi điều chỉnh đấu thầu
Khoản 1. Văn bản scan phải giữ dấu tiếng Việt.
```

Các tiêu chí mẫu đã pass:
- `CỘNG HÒA`
- `Độc lập`
- `Phạm vi điều chỉnh`
- `đấu thầu`

Giới hạn còn lại:
- PaddleOCR 3.x với `lang=vi` vẫn dùng recognizer Latin `latin_PP-OCRv5_mobile_rec`, chưa phải recognizer fine-tune riêng cho tiếng Việt.
- Lớp restore hiện chỉ xử lý các cụm pháp lý/tiêu ngữ phổ biến, không phải bộ sửa dấu tiếng Việt tổng quát.
- Thư mục `models/` trên máy hiện đang thuộc quyền `root`, nên cần chỉnh quyền trước khi prewarm OCR model vào `models/ocr`.

## Mục Tiêu Task Tiếp Theo

Giảm kết quả tìm kiếm trùng lặp khi người dùng upload nhiều file có cùng nội dung hoặc cùng VBHN ở nhiều định dạng PDF/DOCX.

Hiện trạng:
- Người dùng đã xóa dữ liệu upload để upload lại.
- Trước đó search trả nhiều kết quả duplicate vì cùng nội dung tồn tại ở nhiều document/chunk.
- Embedding BKAI local đã chạy được và search semantic đã có score tốt hơn fake embedding.

## Ràng Buộc Không Đổi

- Không dùng cloud service.
- Không đổi stack cố định.
- Docker Compose first.
- MVP first.
- Backend giữ `router -> service -> repository`.
- Frontend giữ `page -> composable -> service -> API`.
- Không hard delete dữ liệu nghiệp vụ nếu chưa có lý do rõ ràng; dùng soft delete.

## Phạm Vi Đề Xuất

### 1. Dedup Ở Cấp Document

Thêm hoặc dùng lại hash nội dung đã trích xuất:
- `source_file_hash`: hash file gốc nếu cần.
- `content_hash`: hash normalized extracted text toàn văn bản.

Khi upload hoặc sau extract:
- Nếu `content_hash` đã tồn tại ở document active khác, đánh dấu duplicate rõ ràng.
- Không tự hard delete bản trùng.
- UI/API có thể hiển thị document duplicate trỏ về document canonical.

### 2. Dedup Ở Cấp Search Result

Trong semantic search response:
- Gom kết quả theo `document_id` hoặc `content_hash`.
- Chọn chunk có score cao nhất làm representative.
- Có thể trả thêm `matched_chunks_count` để biết document có nhiều đoạn match.

MVP nên ưu tiên dedup theo document trước, chưa cần reranker phức tạp.

### 3. Hybrid Search Keyword + Vector

Bổ sung keyword score đơn giản bằng PostgreSQL `ILIKE` hoặc full-text search tiếng Việt tối thiểu.

Score tổng hợp gợi ý:

```text
final_score = vector_score * 0.75 + keyword_score * 0.25
```

Giữ cấu hình weight qua env nếu cần:

```env
SEARCH_VECTOR_WEIGHT=0.75
SEARCH_KEYWORD_WEIGHT=0.25
```

### 4. API Contract

Cập nhật `/api/v1/search/semantic` để response có thêm metadata nếu dedup:

```json
{
  "document_id": "...",
  "chunk_id": "...",
  "score": 0.82,
  "matched_chunks_count": 3,
  "is_deduped": true
}
```

Không phá frontend hiện tại nếu field mới chưa dùng.

### 5. Test

Chuẩn bị 2 file cùng nội dung:
- Một `.txt` hoặc `.docx`.
- Một `.pdf` hoặc file copy cùng text.

Tiêu chí pass:
- Upload cả hai file vẫn xử lý thành công.
- Search `phạm vi điều chỉnh đấu thầu` không trả 5 dòng duplicate giống nhau từ cùng nội dung.
- API vẫn trả được link document nguồn.

## Commit Dự Kiến

```bash
git add apps/api README.md PROJECT_STATUS.md TASK_NEXT.md
git commit -m "feat: deduplicate semantic search results"
```
