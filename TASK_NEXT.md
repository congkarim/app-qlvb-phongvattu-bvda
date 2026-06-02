# Task Tiếp Theo: Tối Ưu OCR Ảnh Scan Thực Tế Và Reranking Search

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-02

## Task Vừa Hoàn Thành

Đã mở rộng fixture OCR tiếng Việt, chạy benchmark trên nhiều mẫu không nhạy cảm và kiểm tra tài liệu thực tế upload từ web.

Kết quả chính:
- Thêm generator deterministic: `tests/fixtures/ocr_vi/generate_fixtures.py`.
- Mở rộng fixture từ 1 mẫu lên 6 mẫu:
  - scan rõ;
  - quyết định hành chính nhiều dấu;
  - scan nén/mờ;
  - trang hai cột và ghi chú;
  - ảnh nghiêng nhẹ có nhiễu;
  - PDF scan 2 trang.
- Mỗi fixture có ground truth `.txt` cùng tên.
- Cập nhật `benchmark_ocr_vi.py` để benchmark cả `.pdf`, gom text nhiều page và báo `seconds_per_page`.
- Cập nhật `tests/fixtures/ocr_vi/README.md` với mô tả fixture và kết quả benchmark.

Benchmark ngày 2026-06-02:

```bash
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker \
  python -m app.scripts.benchmark_ocr_vi \
  --fixtures /app/tests/fixtures/ocr_vi \
  --engine all \
  --format json
```

Tóm tắt kết quả:

| file | paddleocr CER/WER/accent loss | paddle_vietocr CER/WER/accent loss | Nhận xét |
| --- | ---: | ---: | --- |
| `sample_001.png` | 0.0053 / 0.0238 / 0.0294 | 0.0 / 0.0 / 0.0 | VietOCR đạt tuyệt đối trên mẫu rõ. |
| `sample_002.png` | 0.1066 / 0.4722 / 0.4923 | 0.0063 / 0.0417 / 0.0 | VietOCR giữ dấu tốt, còn lỗi dấu câu nhỏ. |
| `sample_003.png` | 0.1443 / 0.5397 / 0.5424 | 0.0687 / 0.1111 / 0.0 | Scan mờ có cải thiện lớn nhưng còn hallucination vài từ. |
| `sample_004.png` | 0.6905 / 0.9783 / 0.4659 | 0.711 / 0.913 / 0.0 | Bố cục hai cột sai thứ tự đọc; đây là lỗi layout/detection, không phải mất dấu. |
| `sample_005.png` | 0.098 / 0.4154 / 0.4808 | 0.0034 / 0.0154 / 0.0 | VietOCR xử lý tốt ảnh nghiêng nhẹ. |
| `sample_006.pdf` | 0.1417 / 0.5487 / 0.5714 | 0.0526 / 0.0531 / 0.0 | PDF scan giữ dấu tốt hơn, còn tách dòng tiêu đề; runtime VietOCR khoảng 39.6s/page. |

Đã kiểm tra:

```bash
docker compose config --quiet
docker compose run --rm --no-deps worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python -m py_compile /app/app/scripts/benchmark_ocr_vi.py /app/tests/fixtures/ocr_vi/generate_fixtures.py
docker compose run --rm --no-deps -e OCR_PREPROCESS_MODE=raw worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --engine all --format json
```

Ghi chú:
- Lệnh benchmark full với `OCR_PREPROCESS_MODE=auto` bị dừng sau hơn 5 phút vì quá chậm cho kiểm tra thường xuyên.

Kiểm tra tài liệu thực tế upload từ web:

| file | trạng thái | OCR/chunk | Nhận xét |
| --- | --- | --- | --- |
| `22-qh-15.signed.pdf` | `searchable`, job `completed` | 84 pages, 184 chunks, avg confidence `0.9272` | Giữ dấu khá tốt, còn lỗi như `LUẶT`, `điều chính`, `dầu khi`, header `869 ? 870`. |
| `0f53863c-d731-4b39-b0ff-d883ab039a88.jpeg` | `searchable`, job `completed` | 1 page, 1 chunk, confidence `0.9037` | Có nhiễu/hallucination: `Thuật`, `Nhất`, `Thành`, `Nhà Tháng`, `Các thuận`; số hiệu/ngày lỗi `72]`, `27IS/2026`. |

Search kiểm tra:
- Query `Lê Thế Anh hồ sơ xin thôi việc Xuân Lâm` trả JPEG mới nhất top 1.
- Query `Luật Đấu thầu phạm vi điều chỉnh` có chunk đúng Điều 1 nhưng chỉ đứng thứ 5.
- Kết quả search còn lẫn bản upload cũ của cùng file PDF, xác nhận cần dedup/reranking.

## Mục Tiêu Task Tiếp Theo

Tối ưu chất lượng OCR cho ảnh scan thực tế và cải thiện ranking search cho văn bản pháp lý đã index.

## Ràng Buộc Không Đổi

- Không dùng cloud OCR.
- Không dùng API LLM để sửa nội dung pháp lý.
- Docker Compose first.
- MVP first.
- Backend giữ `router -> service -> repository`.
- OCR pipeline local/on-prem.
- Không commit model files hoặc runtime artifacts.

## Phạm Vi Đề Xuất

### 1. Tối Ưu OCR Ảnh Scan Thực Tế

Ưu tiên lỗi đã thấy trên JPEG công văn:
- Số hiệu `72]/UBND-KT` cần đọc đúng hơn.
- Ngày `27IS/2026` cần giảm lỗi ký tự ngày tháng.
- Nhiễu từ như `Thuật`, `Nhất`, `Thành`, `Nhà Tháng`, `Các thuận` cần giảm.

Hướng xử lý:
- Thử deskew/denoise nhẹ cho ảnh scan công văn.
- So sánh `raw`, `clahe`, `threshold` trên chính JPEG thực tế.
- Điều chỉnh scoring candidate để ưu tiên text ít nhiễu hơn, không chỉ confidence/accent count.
- Nếu cần, thêm fixture không nhạy cảm mô phỏng nhiễu nền từ ảnh thực tế.

### 2. Tối Ưu Layout Khó Và PDF

Ưu tiên xử lý các lỗi đã thấy trong benchmark:
- `sample_004.png`: trang hai cột bị sai thứ tự đọc.
- `sample_006.pdf`: tiêu đề PDF bị tách dòng không tự nhiên.
- `22-qh-15.signed.pdf`: lỗi header `869 ? 870`, từ `điều chính`, `LUẶT`.
- `OCR_PREPROCESS_MODE=auto`: runtime quá cao trên full fixture.

Hướng xử lý:
- Cải thiện crop ordering theo cột trước khi sort theo dòng.
- Thêm heuristic nối dòng tiêu đề bị tách khi các box cùng hàng.
- Giảm số preprocess candidate khi scan rõ hoặc cho phép benchmark chạy theo mode cụ thể.
- Cache/reuse detector và predictor trong benchmark/service path nếu còn init lặp.

### 3. Dedup/Reranking Search

Vấn đề đã thấy:
- Cùng file `22-qh-15.signed.pdf` tồn tại nhiều bản upload.
- Query đúng ngữ cảnh có chunk Điều 1 nhưng chưa đứng top 1.

Hướng xử lý:
- Dedup kết quả theo `document_id`, `content_hash` hoặc fingerprint gần đúng.
- Rerank ưu tiên chunk có keyword exact match như `Điều 1`, `phạm vi điều chỉnh`, `Luật Đấu thầu`.
- Xem xét hybrid search keyword + vector cho truy vấn pháp lý.

## Tiêu Chí Hoàn Thành

- OCR JPEG công văn giảm rõ lỗi số hiệu/ngày tháng và hallucination từ nhiễu.
- Với layout hai cột, thứ tự đọc không còn trộn cột trái/phải trên fixture hiện có.
- Runtime benchmark có cấu hình kiểm tra nhanh ổn định cho toàn bộ fixture.
- Search `Luật Đấu thầu phạm vi điều chỉnh` đưa chunk Điều 1 lên top 1 hoặc top 2.
- Kết quả search giảm trùng lặp giữa các bản upload cùng nội dung.
- Không phát sinh model/runtime artifact trong git.

## Task Sau Đó Đề Xuất

Khi OCR thực tế đủ ổn:
- Dedup/reranking semantic search để giảm kết quả trùng.
- Hybrid search keyword + vector cho truy vấn pháp lý.

Nếu OCR thực tế vẫn chưa đạt:
- Fine-tune VietOCR hoặc PaddleOCR recognizer trên dataset pháp lý tiếng Việt local.
