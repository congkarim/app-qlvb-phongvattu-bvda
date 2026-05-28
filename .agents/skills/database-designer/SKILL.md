---
name: database-designer
description: Thiết kế PostgreSQL schema, migration, indexes và audit fields cho hệ thống quản lý văn bản OCR.
---

# Database Designer Skill

## Responsibilities

- Thiết kế PostgreSQL schema cho quản lý văn bản, OCR, chunks và nghiệp vụ pháp lý.
- Định nghĩa migration bằng Alembic.
- Thiết kế indexes phục vụ filter, search và join phổ biến.
- Đảm bảo UUID, audit fields và soft delete nhất quán.

## Rules

- Dùng UUID primary key cho bảng nghiệp vụ.
- Mọi bảng nghiệp vụ có `created_at`, `updated_at`, `deleted_at`.
- Dùng soft delete qua `deleted_at`.
- Migration phải rõ ràng, rollback được khi hợp lý.
- Không denormalize sớm nếu chưa có nhu cầu hiệu năng rõ ràng.
- Index theo query thực tế, không tạo index tràn lan.

## Architecture

Database là source of truth cho metadata và trạng thái xử lý. Qdrant chỉ lưu vector và payload phục vụ retrieval.

```text
PostgreSQL: metadata, OCR text, jobs, audit
Qdrant: vectors, searchable payload
Redis: queue/cache/job coordination
```

## Stack

- PostgreSQL
- Alembic
- SQLModel hoặc SQLAlchemy
- UUID
- Timestamp audit fields

## Core Tables

- `documents`
- `document_pages`
- `document_chunks`
- `contracts`
- `dispatches`
- `decisions`
- `audit_logs`

## Modules

- Document metadata schema.
- OCR page result schema.
- Chunk metadata schema.
- Contract/dispatch/decision extension tables.
- User and department references.
- Audit log schema.
- Migration and index planning.

## Coding Conventions

- Primary key field tên là `id`.
- Foreign key đặt tên `{entity}_id`.
- Timestamp dùng timezone-aware type nếu stack hỗ trợ.
- `deleted_at IS NULL` là điều kiện mặc định cho query nghiệp vụ.
- Index thường cần cho `document_type`, `status`, `department_id`, `created_at`, `deleted_at`.
- Bảng `document_chunks` cần index theo `document_id`, `chunk_index` và trạng thái indexing nếu có.
- `audit_logs` nên lưu actor, action, entity type, entity id, timestamp và metadata JSON.
- Không lưu binary file lớn trực tiếp trong PostgreSQL nếu có filesystem/object storage local phù hợp.
