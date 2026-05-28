---
name: ocr-pipeline
description: Thiết kế pipeline OCR local bằng OpenCV và PaddleOCR cho tài liệu PDF hoặc ảnh.
---

# OCR Pipeline Skill

## Responsibilities

- Thiết kế pipeline OCR local/on-prem cho PDF và ảnh scan.
- Chuyển PDF thành image theo từng page.
- Preprocess ảnh bằng OpenCV để cải thiện chất lượng OCR.
- Chạy PaddleOCR, gom text, confidence và tọa độ nếu cần.
- Làm sạch text và kích hoạt bước chunking sau OCR.

## Rules

- Không dùng OCR cloud service.
- Pipeline phải idempotent theo document/page/job.
- Lưu trạng thái từng page để retry độc lập.
- Không làm mất file gốc.
- OCR lỗi một page không được làm hỏng toàn bộ document nếu có thể retry.
- Ghi nhận confidence để phục vụ kiểm tra chất lượng.

## Architecture

```text
upload -> pdf_to_images -> preprocess -> OCR -> clean_text -> persist -> chunk_trigger
```

Trạng thái gợi ý:

```text
pending -> preprocessing -> ocr_running -> ocr_completed -> chunk_pending -> completed
failed -> retry_pending
```

## Stack

- PaddleOCR
- OpenCV
- Python image processing
- PostgreSQL for OCR results and job state
- Redis for queue/job coordination when needed

## Modules

- PDF to image conversion.
- Image preprocessing.
- OCR execution.
- Text cleaning and normalization.
- Confidence calculation.
- Retry and failure handling.
- Chunk trigger integration.

## Coding Conventions

- Preprocess có thể gồm grayscale, denoise, deskew, threshold, resize và contrast adjustment.
- Lưu OCR text theo page trước khi chunk toàn văn bản.
- Confidence phải lưu ở page level và có thể lưu ở block/line level nếu cần.
- Retry logic giới hạn số lần thử, có error reason rõ ràng.
- Text cleaning không được xóa cấu trúc pháp lý quan trọng như `Điều`, `Khoản`, `Mục`, số hiệu và ngày tháng.
- Chunk trigger chỉ chạy khi OCR page cần thiết đã hoàn thành hoặc policy cho phép partial indexing.
- Log duration từng bước để phát hiện bottleneck.
