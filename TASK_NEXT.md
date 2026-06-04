# Task Vừa Hoàn Thành: Xem/Download Source File Khi Sửa Metadata

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã hoàn thành mục tiêu hỗ trợ xem hoặc download tệp nguồn khi người dùng sửa metadata, để có thể đối chiếu số văn bản, ngày ban hành, đơn vị ban hành và loại nghiệp vụ trước khi lưu.

## Kết Quả Chính

- Khi sửa metadata trong trang `/documents/[id]`, người dùng có thể mở lại tệp nguồn để đối chiếu nội dung.
- Luồng sửa metadata vẫn giữ audit log `document.metadata_updated`.
- Không mở rộng sang preview/kiểm soát zip ở bước này.

## Task Tiếp Theo Đề Xuất

1. RBAC nhẹ:
   - Role `admin` và `user`.
   - Chỉ admin được reprocess, xóa source file, đổi source file.
   - User thường chỉ upload/search/xem.

2. Preview file nâng cao:
   - Preview inline PDF/image/text trong trang detail.
   - Fallback download cho DOCX/XLSX hoặc định dạng browser không preview được.
   - Cân nhắc drawer/panel preview cạnh form metadata trên desktop.
