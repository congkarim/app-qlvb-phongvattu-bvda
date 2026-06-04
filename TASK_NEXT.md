# Task Tiếp Theo: Xem/Download Source File Khi Sửa Metadata

Trạng thái: kế hoạch.

Ngày cập nhật: 2026-06-04

## Mục Tiêu

Khi người dùng đang sửa metadata trong `/documents/[id]`, họ vẫn xem được tệp nguồn để đối chiếu số văn bản, ngày ban hành, đơn vị ban hành và loại nghiệp vụ trước khi lưu.

## Phạm Vi MVP

Backend:
- Thêm API xem/download source file:
  - `GET /api/v1/documents/{document_id}/files/{file_id}/download`
- Chỉ trả file còn active và thuộc đúng document.
- Không expose path thật trên server.
- Giữ auth bắt buộc như các document API khác.

Frontend service:
- Thêm method tạo URL xem/download file hoặc gọi API blob.
- Ưu tiên mở file trong tab mới nếu browser hỗ trợ.
- Với file không preview được, fallback download.

UI trang `/documents/[id]`:
- Trong card `Tệp nguồn`, thêm nút `Xem` cạnh từng file.
- Khi đang sửa metadata, vẫn giữ card `Tệp nguồn` dễ truy cập.
- Có thể thêm layout 2 cột trên desktop:
  - Trái: form metadata.
  - Phải: danh sách tệp nguồn hoặc preview link.
- Mobile giữ layout dọc để tránh chật.

Preview MVP:
- PDF/image/text: mở trực tiếp tab mới qua endpoint file.
- DOCX/XLSX: download hoặc mở tab mới tùy browser, chưa cần render nội dung Office.
- ZIP: vẫn tạm không tập trung theo scope trước đó.

## Kiểm Tra Dự Kiến

- Upload hoặc dùng document có nhiều source files.
- Vào detail, bấm `Sửa metadata`.
- Bấm `Xem` một file nguồn:
  - PDF/image/text mở được.
  - DOCX/XLSX download được.
- Lưu metadata sau khi đối chiếu file.
- Audit log vẫn có `document.metadata_updated`.

## Sau Khi Triển Khai

Cập nhật `TASK_NEXT.md` thành:
- Hoàn thành: xem/download source file khi sửa metadata.
- Tiếp theo đề xuất: RBAC nhẹ hoặc preview file nâng cao.
