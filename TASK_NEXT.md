# Task Vừa Hoàn Thành: Xem/Download Source File Khi Sửa Metadata

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã hỗ trợ xem hoặc download tệp nguồn khi người dùng sửa metadata trong `/documents/[id]`, giúp đối chiếu số văn bản, ngày ban hành, đơn vị ban hành và loại nghiệp vụ trước khi lưu.

## Kết Quả Chính

Backend:
- Thêm API:
  - `GET /api/v1/documents/{document_id}/files/{document_file_id}/download`
- Chỉ trả source file còn active và thuộc đúng document.
- Không expose path thật trên server.
- Trả file bằng `FileResponse` với `content-disposition: inline`.
- File id sai hoặc file không tồn tại trả 404.

Frontend:
- `document.service.ts` có `downloadSourceFile` dùng auth header để fetch blob.
- `useDocuments.ts` có `openSourceFile` và `sourceFileViewLoading`.
- Trang `/documents/[id]` có nút `Xem` cạnh từng tệp nguồn.
- PDF/image/text mở tab mới; DOCX/XLSX hoặc định dạng browser không preview được fallback download.

## Đã Kiểm Tra

```bash
docker compose config --quiet
docker compose run --rm --no-deps api python -m py_compile app/repositories/document_repository.py app/services/document_service.py app/routers/documents.py
docker compose run --rm --no-deps web npm run build
curl -fsS -I http://localhost:3000/login
curl -fsS -I http://localhost:3000/documents/{document_id}
```

Kết quả:
- Backend compile pass.
- Frontend build pass qua Docker.
- Download source file hợp lệ trả 200 với `content-disposition: inline`.
- File id sai trả 404.
- `/login` trả 200.
- Detail route redirect `302 /login` khi chưa đăng nhập.

## Task Tiếp Theo Đề Xuất

1. RBAC nhẹ:
   - Role `admin` và `user`.
   - Chỉ admin được reprocess, xóa source file, đổi source file.
   - User thường chỉ upload/search/xem.

2. Preview file nâng cao:
   - Preview inline PDF/image/text trong trang detail.
   - Fallback download cho DOCX/XLSX hoặc định dạng browser không preview được.
   - Cân nhắc drawer/panel preview cạnh form metadata trên desktop.
