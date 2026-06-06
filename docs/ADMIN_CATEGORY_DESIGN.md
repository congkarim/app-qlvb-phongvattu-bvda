# Admin Category Design

Cập nhật ngày: 2026-06-06

## Mục Tiêu

Thiết kế danh mục admin tối thiểu cho Phase 5 để các option nghiệp vụ không còn phải sửa trực tiếp trong code frontend.

Danh mục cần quản lý trong MVP:
- Đơn vị/phòng ban.
- Loại nghiệp vụ.
- Loại văn bản.

Ngoài scope MVP:
- Workflow phê duyệt thay đổi danh mục.
- Versioning danh mục.
- Rule engine hoặc cấu hình động cho toàn hệ thống.
- Inventory/procurement catalog chi tiết.

## Quyết Định Thiết Kế

### 1. Đơn Vị/Phòng Ban

Dùng bảng `departments` hiện có làm source of truth.

Lý do:
- `departments` đã liên kết với `users.department_id` và `documents.department_id`.
- Đây là entity nghiệp vụ riêng, không nên gom vào bảng option generic.
- Model hiện có đã dùng UUID, `created_at`, `updated_at`, `deleted_at`.

Trường tối thiểu cho CRUD admin:
- `id`.
- `code`.
- `name`.
- `created_at`, `updated_at`, `deleted_at`.

Trường có thể bổ sung khi làm migration nếu cần UI tốt hơn:
- `description`.
- `sort_order`.
- `is_active`.

Seed MVP đề xuất:
- `VT` - Phòng Vật tư.
- `UNKNOWN` - Chưa xác định.

### 2. Loại Nghiệp Vụ

Dùng bảng catalog item giới hạn cho các option dạng `code`/`label`, không tạo framework cấu hình chung.

Tên bảng đề xuất cho mục tiêu CRUD tiếp theo:
- `admin_catalog_items`.

Giá trị `catalog_type`:
- `business_type`.
- `document_type`.

Trường tối thiểu:
- `id`.
- `catalog_type`.
- `code`.
- `label`.
- `description`.
- `sort_order`.
- `is_active`.
- `created_at`, `updated_at`, `deleted_at`.

Ràng buộc đề xuất:
- Unique active theo `(catalog_type, code)` khi `deleted_at IS NULL`.
- Index `(catalog_type, is_active, sort_order)`.
- Không hard delete.

Seed MVP cho `business_type`:
- `incoming_dispatch` - Công văn đến.
- `outgoing_dispatch` - Công văn đi.
- `contract` - Hợp đồng.
- `decision` - Quyết định.

### 3. Loại Văn Bản

Dùng cùng bảng `admin_catalog_items` với `catalog_type = document_type`.

Lý do:
- Loại văn bản hiện là option dạng mã/nhãn, không cần bảng quan hệ riêng.
- Các mã đang gắn với OCR classifier và metadata document, nên cần source of truth thống nhất.
- Không thay đổi classifier trong mục tiêu thiết kế này; classifier vẫn có fallback khi gặp mã chưa có trong catalog.

Seed MVP cho `document_type` lấy từ option hiện có:
- `UNKNOWN` - Không đủ dữ liệu.
- `NQ` - Nghị quyết.
- `QĐ` - Quyết định.
- `CT` - Chỉ thị.
- `QC` - Quy chế.
- `QYĐ` - Quy định.
- `TC` - Thông cáo.
- `TB` - Thông báo.
- `HD` - Hướng dẫn.
- `CTr` - Chương trình.
- `KH` - Kế hoạch.
- `PA` - Phương án.
- `ĐA` - Đề án.
- `DA` - Dự án.
- `BC` - Báo cáo.
- `BB` - Biên bản.
- `TTr` - Tờ trình.
- `HĐ` - Hợp đồng.
- `CV` - Công văn.
- `CĐ` - Công điện.
- `BGN` - Bản ghi nhớ.
- `BTT` - Bản thỏa thuận.
- `GUQ` - Giấy ủy quyền.
- `GM` - Giấy mời.
- `GGT` - Giấy giới thiệu.
- `GNP` - Giấy nghỉ phép.
- `PG` - Phiếu gửi.
- `PC` - Phiếu chuyển.
- `PB` - Phiếu báo.
- `TCg` - Thư công.

## API Boundary Đề Xuất

Read option cho user đã đăng nhập:
- `GET /api/v1/catalogs/departments`.
- `GET /api/v1/catalogs/business-types`.
- `GET /api/v1/catalogs/document-types`.

CRUD admin-only:
- `POST /api/v1/admin/catalogs/departments`.
- `PATCH /api/v1/admin/catalogs/departments/{id}`.
- `DELETE /api/v1/admin/catalogs/departments/{id}`.
- `POST /api/v1/admin/catalogs/items`.
- `PATCH /api/v1/admin/catalogs/items/{id}`.
- `DELETE /api/v1/admin/catalogs/items/{id}`.

Audit log actions:
- `admin_catalog.department_created`.
- `admin_catalog.department_updated`.
- `admin_catalog.department_deleted`.
- `admin_catalog.item_created`.
- `admin_catalog.item_updated`.
- `admin_catalog.item_deleted`.

## Frontend Boundary Đề Xuất

Giữ luồng:

```text
page -> composable -> service -> API
```

Thêm ở mục tiêu sau:
- `apps/web/types/catalog.ts`.
- `apps/web/services/catalog.service.ts`.
- `apps/web/composables/useCatalogs.ts`.
- Trang admin `/admin/catalogs` hoặc tab trong khu vực admin hiện có.

Các form cần đổi từ hardcode sang API ở mục tiêu Phase 5 / Mục tiêu 3:
- `/upload`: `business_type`.
- `/documents`: filter `business_type`, `document_type`.
- `/documents/[id]`: form metadata `business_type`, `document_type`.
- `/dashboard`: filter semantic search `business_type`.

Fallback khi API lỗi:
- Giữ option hardcoded hiện tại trong frontend service/composable làm fallback.
- Không chặn upload hoặc search khi catalog API lỗi.
- Nếu document cũ có mã không còn active, UI vẫn hiển thị mã cũ thay vì mất dữ liệu.

## Tiêu Chí Cho Mục Tiêu CRUD Tiếp Theo

- Migration chỉ thêm phần cần cho danh mục MVP.
- Router không chứa business logic.
- Service validate code, normalize label, ghi audit.
- Repository lọc mặc định `deleted_at IS NULL`.
- Admin-only cho create/update/delete.
- Read catalog cho user đã đăng nhập để frontend lấy option.
- Soft delete, không hard delete.
