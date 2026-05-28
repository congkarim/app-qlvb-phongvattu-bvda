# Legal Document AI Agents

Hệ thống này dùng Codex Agent Skills để hỗ trợ phát triển local/on-prem cho quản lý văn bản, OCR và semantic search. Không viết lệch khỏi stack cố định khi chưa có yêu cầu rõ ràng.

## Stack Cố Định

Backend:
- FastAPI
- PostgreSQL
- Redis
- Qdrant
- PaddleOCR
- OpenCV

Frontend:
- Nuxt 3
- TypeScript
- PrimeVue
- TailwindCSS
- Pinia

Deploy:
- Docker Compose

## Quy Tắc

- Không dùng cloud service.
- Không tự đổi stack.
- Không over-engineering.
- Docker Compose first.
- MVP first.
- Router không chứa business logic.
- Frontend không gọi API trực tiếp trong component.
- Component phải tái sử dụng.
- Ưu tiên maintainability.
- Khi hoàn thành task, dùng skill `project-git-manager` để cập nhật trạng thái repo, tài liệu tiến độ và commit thay đổi liên quan nếu repo đã sẵn sàng.

## Kiến Trúc

Backend:

```text
router -> service -> repository
```

Frontend:

```text
page -> composable -> service -> API
```

## OCR Pipeline

```text
upload -> preprocess -> OCR -> chunk -> embedding -> qdrant
```

## Database

- UUID primary key.
- Mọi bảng nghiệp vụ có `created_at`, `updated_at`.
- Dùng `deleted_at` cho soft delete.
- Không hard delete dữ liệu nghiệp vụ nếu chưa có lý do rõ ràng.
