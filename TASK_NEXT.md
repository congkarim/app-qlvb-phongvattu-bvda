# Task Vừa Hoàn Thành: Preview File Inline Trong Document Detail

Trạng thái: hoàn thành.

Ngày cập nhật: 2026-06-04

## Phạm Vi Đã Thực Hiện

Đã thêm preview inline cho tệp nguồn trong trang `/documents/[id]` để người dùng đối chiếu file gốc với metadata, OCR text và chunks ngay trong detail page.

Luồng frontend vẫn giữ đúng kiến trúc:

```text
page -> composable -> service -> API
```

## Kết Quả Chính

Frontend:
- Thêm type `SourceFilePreview` và `SourceFilePreviewMode`.
- `document.service.ts` tiếp tục là lớp gọi API/blob có auth.
- `useDocuments()` quản lý state preview:
  - `sourceFilePreview`
  - `sourceFilePreviewLoading`
  - `previewSourceFile()`
  - `clearSourceFilePreview()`
- Trang `/documents/[id]` trong card `Tệp nguồn` có:
  - Nút `Xem trước` để preview inline.
  - Nút `Mở` để mở tab mới hoặc download như trước.
  - PDF render bằng `iframe`.
  - Ảnh render bằng `img`.
  - Text render bằng `pre`.
  - DOCX/XLSX hoặc định dạng không preview được fallback download.
- Object URL được revoke khi đóng preview, đổi/xóa/thêm file nguồn hoặc rời trang.

Docs:
- Cập nhật `README.md`.
- Cập nhật `PROJECT_STATUS.md`.

## Đã Kiểm Tra

```bash
docker compose run --rm --no-deps web npm run build
```

Kết quả:
- Frontend build pass.
- Vẫn có warning chunk PrimeVue lớn như trước, không fail.

## Task Tiếp Theo Đề Xuất

1. Metadata chunk trong PostgreSQL nếu cần UI chi tiết:
   - Thêm migration cho `section_role`, `section_path`, `doc_group`, `requires_review`.
   - Hiển thị role/path/confidence trong trang document detail.

2. RBAC nhẹ:
   - Role `admin` và `user`.
   - Chỉ admin được reprocess, xóa source file, đổi thứ tự source file.
   - User thường chỉ upload/search/xem/sửa metadata theo quyền được cấp.
