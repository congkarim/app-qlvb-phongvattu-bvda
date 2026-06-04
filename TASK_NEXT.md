# Task Vừa Hoàn Thành: Sửa Metadata Sau Upload

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã triển khai sửa metadata nghiệp vụ sau upload theo task ưu tiên trong kế hoạch. Phần preview/kiểm soát zip vẫn tạm để sau.

## Kết Quả Chính

Backend:
- Thêm request DTO `DocumentMetadataUpdateRequest`.
- Thêm API `PATCH /api/v1/documents/{document_id}/metadata`.
- Service cập nhật:
  - `title`
  - `document_number`
  - `issued_date`
  - `issuing_agency`
  - `business_type`
- Repository có method cập nhật metadata riêng, không đặt business logic trong router.
- Mỗi lần lưu metadata ghi audit log `document.metadata_updated`, gồm `changed_fields`, `previous`, `current`.

Frontend:
- `document.service.ts` có `updateMetadata`.
- `useDocuments.ts` có `updateDocumentMetadata` và `metadataLoading`.
- Trang `/documents/[id]` có chế độ sửa trong card `Metadata`.
- Form cho phép sửa tên văn bản, số văn bản, ngày ban hành, đơn vị ban hành và loại nghiệp vụ.
- Lưu thành công refresh detail để hiển thị audit log mới.

## Đã Kiểm Tra

```bash
docker compose config --quiet
docker compose run --rm --no-deps api python -m py_compile app/schemas/document.py app/repositories/document_repository.py app/services/document_service.py app/routers/documents.py
docker compose run --rm --no-deps web npm run build
curl -fsS -I http://localhost:3000/login
curl -fsS -I http://localhost:3000/documents/{document_id}
```

Kết quả:
- Backend compile pass.
- Frontend build pass qua Docker.
- `PATCH /api/v1/documents/419a80f8-dc60-4148-a62d-c55a6acf6bc9/metadata` cập nhật đúng:
  - title: `Metadata smoke updated`
  - document_number: `456/CV-VT`
  - issuing_agency: `Phòng Vật tư cập nhật`
  - business_type: `outgoing_dispatch`
- Detail response có audit log mới nhất `document.metadata_updated`.
- `/login` trả 200.
- Detail route redirect `302 /login` khi chưa đăng nhập.

## Giới Hạn Còn Lại

- Chưa có batch zip: một zip chứa nhiều văn bản riêng.
- Chưa có preview nội dung zip trước khi upload.
- Chưa có kéo thả reorder; hiện dùng nút lên/xuống.
- Chưa có khôi phục source file đã soft-delete.
- Metadata hiện là field chung trên `documents`, chưa tách bảng riêng cho công văn/hợp đồng/quyết định.
- Chưa có RBAC role admin/user.

## Task Tiếp Theo Đề Xuất

Ưu tiên tiếp theo nên là một trong các hướng sau:

1. RBAC nhẹ:
   - Role `admin` và `user`.
   - Chỉ admin được reprocess, xóa source file, đổi source file.
   - User thường chỉ upload/search/xem.

2. Preview và kiểm soát zip, tạm để sau:
   - Xem danh sách file trong zip trước khi tạo document.
   - Cho phép bỏ chọn file trong zip.
   - Cảnh báo file unsupported trước OCR.

3. Metadata nghiệp vụ chuyên sâu:
   - Tách bảng riêng cho công văn/hợp đồng/quyết định khi workflow thực tế đủ rõ.
   - Bổ sung validation nghiệp vụ theo từng loại.
