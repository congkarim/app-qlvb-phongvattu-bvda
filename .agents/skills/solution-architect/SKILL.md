---
name: solution-architect
description: Giữ consistency kiến trúc toàn hệ thống, MVP scope, Docker Compose first và module boundaries.
---

# Solution Architect Skill

## Responsibilities

- Giữ consistency toàn hệ thống giữa backend, frontend, OCR, search và database.
- Chống over-engineering.
- Bảo vệ scope MVP.
- Định nghĩa module boundaries rõ ràng.
- Đảm bảo mọi quyết định phù hợp local/on-prem và Docker Compose first.

## Rules

- Không dùng cloud service.
- Không đổi stack khi chưa có yêu cầu rõ ràng.
- Docker Compose first.
- MVP first.
- Ưu tiên maintainability hơn abstraction phức tạp.
- Không thêm service mới nếu PostgreSQL, Redis hoặc Qdrant đã đáp ứng đủ.
- Thiết kế phải vận hành được trong môi trường nội bộ.

## Architecture

Luồng hệ thống chính:

```text
Frontend Nuxt -> FastAPI -> PostgreSQL/Redis/Qdrant -> OCR/Embedding workers
```

Luồng xử lý tài liệu:

```text
upload -> persist metadata -> OCR job -> page OCR -> chunk -> embed -> qdrant -> searchable
```

## Stack

- FastAPI
- PostgreSQL
- Redis
- Qdrant
- PaddleOCR
- OpenCV
- Nuxt 3
- TypeScript
- PrimeVue
- TailwindCSS
- Pinia
- Docker Compose

## Modules

- Identity and access.
- Document management.
- OCR pipeline.
- Semantic search and RAG.
- Legal document subdomains: contracts, dispatches, decisions.
- Audit logging.
- Admin configuration.

## Coding Conventions

- Backend module boundary phải theo nghiệp vụ, không gom tất cả vào shared service.
- Shared utilities chỉ chứa logic thật sự dùng lại nhiều nơi.
- Router không chứa business logic.
- Frontend component không gọi API trực tiếp.
- Database schema phải hỗ trợ soft delete và audit ngay từ đầu.
- Search phải luôn trả source để người dùng truy vết về tài liệu gốc.
- Ưu tiên thiết kế đơn giản có thể mở rộng sau khi có nhu cầu thật.
- Mọi quyết định kiến trúc lớn cần ghi rõ tradeoff và ảnh hưởng vận hành.
