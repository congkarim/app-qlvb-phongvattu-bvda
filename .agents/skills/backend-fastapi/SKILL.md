---
name: backend-fastapi
description: Xây dựng backend FastAPI cho hệ thống quản lý văn bản OCR và semantic search.
---

# Backend FastAPI Skill

## Responsibilities

- Thiết kế và triển khai API backend cho quản lý văn bản pháp lý.
- Xây dựng auth JWT, phân quyền cơ bản, users và departments.
- Xử lý upload file, metadata tài liệu, OCR jobs và trạng thái xử lý.
- Cung cấp search APIs cho keyword search, semantic search và metadata filtering.
- Giữ business logic trong service layer, không đặt trong router.

## Rules

- Dùng FastAPI, SQLModel hoặc SQLAlchemy, Alembic.
- Không dùng cloud service.
- Không tự đổi PostgreSQL, Redis, Qdrant.
- Không over-engineering trước MVP.
- API response rõ ràng, thống nhất, dễ debug.
- Router chỉ nhận request, validate input và gọi service.
- Repository chỉ làm việc với database query/persistence.
- Service xử lý business logic, transaction boundary và orchestration.

## Architecture

```text
router -> service -> repository
```

Khuyến nghị module nội bộ:

```text
app/modules/{module_name}/
  router.py
  service.py
  repository.py
  schemas.py
  models.py
```

## Stack

- FastAPI
- SQLModel hoặc SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Qdrant
- PaddleOCR integration
- OpenCV integration
- JWT auth

## Modules

- `auth`: login, refresh token, password hashing, JWT validation.
- `users`: tài khoản, trạng thái, thông tin người dùng.
- `departments`: phòng ban, đơn vị xử lý văn bản.
- `documents`: tài liệu chung, upload file, metadata, pages, chunks.
- `contracts`: hợp đồng và metadata nghiệp vụ.
- `dispatches`: công văn đến/đi và metadata nghiệp vụ.
- `decisions`: quyết định và metadata nghiệp vụ.
- `search`: keyword search, semantic search, filters, result ranking.
- `audit_logs`: log thao tác nghiệp vụ quan trọng.

## Coding Conventions

- Dùng UUID primary key cho entity nghiệp vụ.
- Mọi bảng nghiệp vụ có `created_at`, `updated_at`, `deleted_at`.
- Dùng soft delete qua `deleted_at`.
- DTO/request/response đặt trong `schemas.py`.
- Không expose trực tiếp ORM model nếu không cần thiết.
- File upload phải kiểm tra extension, MIME type và size.
- OCR jobs nên chạy async/background qua Redis-backed queue khi MVP cần.
- Không block request upload bằng OCR dài nếu tài liệu lớn.
- Search API phải hỗ trợ pagination, filters và sort ổn định.
- Log lỗi đủ ngữ cảnh nhưng không ghi token, password hoặc dữ liệu nhạy cảm.
