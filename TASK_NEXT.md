# Task Tiếp Theo: Tối Ưu PDF Scan Và Hybrid Search

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-02

## Task Vừa Hoàn Thành

Đã tối ưu OCR ảnh scan thực tế, layout hai cột và reranking/dedup search mức MVP.

Kết quả chính:
- Thêm column-aware line ordering cho VietOCR:
  - Trang hai cột được đọc theo cột trái trước, rồi cột phải.
  - Có guard để không áp dụng column-sort nhầm cho công văn một cột có header hai bên.
- Thêm cleanup OCR hẹp cho lỗi thực tế đã thấy:
  - `Số: 72]/UBND-KT` -> `Số: 72/UBND-KT`.
  - `27IS/2026`, `Thứ 2715/2026` -> `27/5/2026`.
  - `Thông bảo` -> `Thông báo`.
  - Giảm nhiễu như `Thuật`, `Nhất`, `Thành`, `Nhà Tháng`, `Các thuận`, `thuận thuận`, `1990`, `1992`, `E`, `16`, `6n`, `2`.
- Thêm reranking/dedup search:
  - Search lấy nhiều hit hơn từ Qdrant rồi rerank nội bộ.
  - Boost exact legal markers như `Điều 1`, `phạm vi điều chỉnh`, `Luật Đấu thầu`.
  - Giảm kết quả yếu trùng theo document/title/text.
  - Thêm `content_hash` vào Qdrant payload cho index/reindex sau.

Đã kiểm tra:

```bash
docker compose run --rm --no-deps worker python -m py_compile /app/app/services/document_content_service.py /app/app/services/ocr/paddle_vietocr_engine.py /app/app/services/search_service.py /app/app/workers/ocr_worker.py /app/app/scripts/reindex_embeddings.py
```

OCR fixture hai cột `sample_004.png` với `OCR_PREPROCESS_MODE=raw`, `paddle_vietocr`:

```text
PHỤ LỤC QUY TRÌNH KIỂM SOÁT VẬT TƯ
Điều 5. Kiểm kê vật tư
1. Kho vật tư thực hiện kiểm kê định
kỳ vào ngày cuối quý
2. Biên bản kiểm kê phải có chữ ký của
thủ kho và kế toán.
3. Vật tư hư hỏng được lập danh sách
riêng để xử lý
Điều 6. Báo cáo sử dụng
1. Báo cáo gửi về phòng vật tư trước
ngày 05 hằng tháng.
2. Số liệu báo cáo phải khớp với phiếu
xuất, phiếu nhập
Ghi chú: Không tự ý điều chuyển vật
tư giữa các công trình.
```

OCR lại JPEG công văn xã Xuân Lâm:

```text
confidence=0.9043
Số: 72/UBND-KT
Xuân Lâm, ngày 26 tháng 5 năm 2026
Kính gửi: Ban chỉ huy 32 xóm.
...
bất kỳ các hồ sơ thuộc các lĩnh vực cho Đồng chí Lê Thế Anh kể từ ngày
27/5/2026; đối với các hồ sơ đã được người dân nộp trực tiếp cho Đồng chí Lê
...
Thông báo và tuyên truyền đến toàn thể nhân dân không trực tiếp nộp
```

Search:

```bash
curl -fsS -X POST http://localhost:8000/api/v1/search/semantic \
  -H 'Content-Type: application/json' \
  -d '{"query":"Luật Đấu thầu phạm vi điều chỉnh","limit":5}'
```

Kết quả:
- Chunk `Điều 1. Phạm vi điều chính` lên top 2.
- Top 5 không còn lẫn các bản upload cũ của cùng file PDF.

## Mục Tiêu Task Tiếp Theo

Tối ưu phần còn lại của OCR PDF scan và cải thiện search pháp lý exact-match lên top 1 ổn định hơn.

## Ràng Buộc Không Đổi

- Không dùng cloud OCR.
- Không dùng API LLM để sửa nội dung pháp lý.
- Docker Compose first.
- MVP first.
- Backend giữ `router -> service -> repository`.
- OCR pipeline local/on-prem.
- Không commit model files hoặc runtime artifacts.

## Phạm Vi Đề Xuất

### 1. Tối Ưu PDF/Header Scan

Vấn đề còn lại:
- `22-qh-15.signed.pdf`: header `CÔNG BÁO/SỐ 869 ? 870` còn sai dấu phân tách.
- Một số lỗi từ vẫn còn: `LUẶT`, `điều chính`, `dầu khi`.
- `sample_006.pdf`: tiêu đề bị tách dòng không tự nhiên.

Hướng xử lý:
- Thêm heuristic nối line tiêu đề khi các box cùng hàng hoặc cùng cụm header.
- Bổ sung cleanup pháp lý hẹp cho các lỗi phổ biến trên PDF scan.
- Kiểm tra riêng page 1 và một số page có header/footer nhiều nhiễu.

### 2. Giảm Runtime Benchmark/OCR Auto

Vấn đề:
- `OCR_PREPROCESS_MODE=auto` full fixture quá chậm cho vòng kiểm tra thường xuyên.

Hướng xử lý:
- Cho benchmark chạy theo danh sách fixture hoặc giới hạn file/page.
- Chỉ thử `raw/clahe/threshold` khi scoring nhanh thấy cần.
- Cache/reuse detector/predictor trong benchmark path nếu còn init lặp.

### 3. Hybrid Search Keyword + Vector

Vấn đề:
- Query `Luật Đấu thầu phạm vi điều chỉnh` đã lên top 2, nhưng chưa top 1.

Hướng xử lý:
- Thêm keyword scorer rõ ràng hơn cho `section_title`, `Điều`, `Khoản`, số hiệu.
- Có thể bổ sung PostgreSQL keyword candidate trước khi merge với Qdrant vector hits.
- Tiếp tục dedup theo `content_hash` sau khi reindex payload mới.

## Tiêu Chí Hoàn Thành

- PDF page 1 giảm lỗi header và từ pháp lý phổ biến.
- Benchmark có chế độ kiểm tra nhanh theo fixture/file cụ thể.
- Search `Luật Đấu thầu phạm vi điều chỉnh` đưa chunk Điều 1 lên top 1 ổn định.
- Không phát sinh model/runtime artifact trong git.

## Task Sau Đó Đề Xuất

- Reindex Qdrant để payload mới có `content_hash`.
- Thêm bộ fixture ảnh scan công văn không nhạy cảm mô phỏng nhiễu thực tế.
- Cân nhắc fine-tune VietOCR hoặc recognizer local nếu vẫn còn lỗi OCR khó.
