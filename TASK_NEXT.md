# Task Tiếp Theo: Mở Rộng Fixture OCR Và Kiểm Tra Tài Liệu Thực Tế

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-01

## Task Vừa Hoàn Thành

Đã tích hợp VietOCR local cho OCR tiếng Việt.

Kết quả chính:
- Thêm dependency `vietocr==0.3.13` và `torchvision==0.17.2+cpu`.
- Hạ `Pillow` xuống `10.2.0` để thỏa dependency VietOCR.
- Thêm config:
  - `OCR_ENGINE=paddle_vietocr`
  - `VIETOCR_MODEL_DIR`
  - `VIETOCR_DEVICE`
  - `VIETOCR_CONFIG`
  - `VIETOCR_WEIGHT_PATH`
  - `VIETOCR_MAX_BATCH_SIZE`
  - `VIETOCR_BEAMSEARCH`
- Tách OCR engine module:
  - `app/services/ocr/schemas.py`
  - `app/services/ocr/paddle_ocr_engine.py`
  - `app/services/ocr/paddle_vietocr_engine.py`
- Luồng `paddle_vietocr`:
  - PaddleOCR detect text boxes.
  - Crop từng line bằng perspective transform.
  - VietOCR recognize crop tiếng Việt.
  - DocumentContentService clean text và chọn preprocess candidate tốt nhất.
- Giữ `OCR_ENGINE=paddleocr` làm baseline/fallback thủ công.
- Thêm benchmark script `app/scripts/benchmark_ocr_vi.py`.
- Thêm fixture mẫu không nhạy cảm tại `tests/fixtures/ocr_vi`.
- Chuẩn bị model local bị ignore bởi git:
  - `models/ocr/vietocr/transformerocr.pth`
  - `models/ocr/PP-OCRv5_server_det`
  - `models/ocr/latin_PP-OCRv5_mobile_rec`

Benchmark fixture `sample_001.png`:

```text
paddleocr: CER 0.0053, WER 0.0238, accent loss 0.0294, 34.944s
paddle_vietocr: CER 0.0, WER 0.0, accent loss 0.0, 49.487s
```

OCR mẫu với default `OCR_ENGINE=paddle_vietocr`:

```text
confidence=0.9259
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
Điều 1. Phạm vi điều chỉnh đấu thầu
Khoản 1. Văn bản scan phải giữ dấu tiếng Việt.
Số 74/VBHN-VPQH ngày 15 tháng 5 năm 2025.
```

Đã kiểm tra:

```bash
docker compose config
docker compose build api worker
docker compose up -d api worker
docker compose exec -T worker sh -lc 'python -m py_compile /app/app/core/config.py /app/app/services/document_content_service.py /app/app/services/ocr/*.py /app/app/scripts/benchmark_ocr_vi.py'
curl -fsS http://localhost:8000/health
docker compose exec -T worker python -m app.scripts.benchmark_ocr_vi --fixtures /app/tests/fixtures/ocr_vi --engine all --format json
```

## Mục Tiêu Task Tiếp Theo

Mở rộng kiểm tra OCR trên tài liệu thực tế người dùng upload lại, đặc biệt PDF scan pháp lý, để xác nhận VietOCR cải thiện đủ trong điều kiện thật.

## Ràng Buộc Không Đổi

- Không dùng cloud OCR.
- Không dùng API LLM để sửa nội dung pháp lý.
- Docker Compose first.
- MVP first.
- Backend giữ `router -> service -> repository`.
- OCR pipeline local/on-prem.
- Không commit model files hoặc runtime artifacts.

## Phạm Vi Đề Xuất

### 1. Mở Rộng Fixtures

Thêm 5-10 ảnh/PDF scan không nhạy cảm:
- Scan rõ.
- Scan mờ/nén.
- Trang nhiều cột hoặc nhiều footnote nếu có.
- Mẫu văn bản có số hiệu, ngày tháng, điều/khoản.

Mỗi file có ground truth `.txt` cùng tên.

### 2. Chạy Benchmark Lại

Command:

```bash
docker compose exec -T worker python -m app.scripts.benchmark_ocr_vi \
  --fixtures /app/tests/fixtures/ocr_vi \
  --engine all
```

Ghi nhận:
- CER.
- WER.
- Accent loss.
- Runtime/page.
- Lỗi số hiệu/ngày tháng/điều khoản.

### 3. Upload Lại Tài Liệu Thực Tế

Sau khi người dùng upload lại file thực tế:
- Theo dõi worker log.
- Kiểm tra OCR page text.
- Kiểm tra chunk/search.
- Ghi lại file/page nào vẫn lỗi dấu hoặc sai số hiệu.

### 4. Tối Ưu Nếu Cần

Nếu VietOCR chậm:
- Giảm số preprocess candidate khi scan rõ.
- Chỉ dùng `raw/clahe` thay vì `auto`.
- Cache detector/predictor theo process đã có, tránh init lại.

Nếu detection box sai:
- Cải thiện crop ordering.
- Điều chỉnh render scale PDF.
- Thử deskew trước OCR.

## Tiêu Chí Hoàn Thành

- Có benchmark trên nhiều hơn một fixture.
- Có nhận xét rõ VietOCR đạt/chưa đạt với tài liệu thực tế.
- Nếu còn lỗi, có danh sách lỗi cụ thể theo file/page.
- Không phát sinh model/runtime artifact trong git.

## Task Sau Đó Đề Xuất

Khi OCR thực tế đủ ổn:
- Dedup/reranking semantic search để giảm kết quả trùng.
- Hybrid search keyword + vector cho truy vấn pháp lý.

Nếu OCR thực tế vẫn chưa đạt:
- Fine-tune VietOCR hoặc PaddleOCR recognizer trên dataset pháp lý tiếng Việt local.
