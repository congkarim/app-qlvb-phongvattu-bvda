# Domain Module Decision

Cập nhật lần cuối: 2026-06-06

## Module Đầu Tiên

Chọn module đầu tiên cho Phase 4: **Hợp đồng và phụ lục hợp đồng**.

## Lý Do Chọn

- Phòng vật tư thường cần tra cứu hợp đồng, phụ lục, danh mục vật tư, điều khoản nghiệm thu, thanh toán, bảo hành và nhà cung cấp.
- Module này tận dụng trực tiếp nền hiện có: upload nhiều file cùng văn bản, OCR, legal-aware chunking, `section_role=appendix`, semantic search và RAG citation.
- Hệ thống đã có `business_type=contract` trong upload/search/UI và benchmark search đã có fixture hợp đồng/phụ lục.
- Chunking hiện có đã xếp nhóm hợp đồng vào nhóm C và ưu tiên cắt theo `Điều`, phù hợp retrieval theo điều khoản.
- Scope metadata có thể giữ gọn quanh document core, không kéo sang inventory workflow hoặc quản lý mua sắm đầy đủ ở MVP.

## Ứng Viên Chưa Chọn

- Công văn đến/đi: đã được document core và metadata nghiệp vụ hiện có bao phủ tương đối tốt; module riêng có giá trị nhưng ít tạo thêm cấu trúc mới ngay.
- Quyết định/thông báo/đề nghị mua sắm: quan trọng cho tra cứu pháp lý nội bộ, nhưng workflow ban đầu giống document core hơn hợp đồng.
- Phiếu/đề xuất vật tư: có thể có giá trị cao, nhưng dễ kéo sang inventory/procurement workflow, vượt scope MVP hiện tại.

## Scope MVP

MVP chỉ quản lý hồ sơ hợp đồng như một lớp nghiệp vụ liên kết document core, không thay thế OCR/search/document workflow.

Metadata tối thiểu:

- `document_id`: liên kết 1-1 tới `documents`.
- `contract_number`: số hợp đồng hoặc số tham chiếu.
- `contract_title`: tên hợp đồng nghiệp vụ, mặc định lấy từ document title nếu chưa nhập.
- `supplier_name`: nhà cung cấp/đối tác.
- `sign_date`: ngày ký.
- `effective_from`, `effective_to`: hiệu lực hợp đồng.
- `contract_value`: giá trị hợp đồng nếu có.
- `currency`: mặc định `VND`.
- `status`: `draft`, `active`, `expired`, `terminated`, `completed`.
- `notes`: ghi chú ngắn.

Workflow MVP:

- Admin/user có quyền hiện tại upload hoặc chọn document đã có `business_type=contract`.
- Tạo/cập nhật metadata hợp đồng liên kết với document.
- List/filter hợp đồng theo số hợp đồng, nhà cung cấp, trạng thái, ngày ký/hiệu lực và document liên quan.
- Detail hợp đồng hiển thị metadata, link document nguồn, chunks/phụ lục liên quan và dùng search/RAG hiện có để truy vấn điều khoản.
- Audit log cho create/update/delete mềm metadata hợp đồng.

Không làm trong MVP:

- Không quản lý inventory, yêu cầu mua sắm, thanh toán hoặc nghiệm thu theo workflow nhiều bước.
- Không tạo bảng dòng hàng vật tư chi tiết nếu chưa có nhu cầu thật.
- Không tự động trích xuất tất cả trường hợp đồng bằng LLM.
- Không thêm service ngoài PostgreSQL/Qdrant/Redis hiện có.

## Boundary Kỹ Thuật

Backend:

```text
router -> service -> repository
```

- Module hợp đồng có router/service/repository riêng.
- Bảng nghiệp vụ dùng UUID primary key, `created_at`, `updated_at`, `deleted_at`.
- Không hard delete metadata hợp đồng.
- Liên kết document core qua `document_id`, không copy OCR text/chunk sang bảng module.

Frontend:

```text
page -> composable -> service -> API
```

- Page module hợp đồng dùng service/composable riêng.
- Không gọi API trực tiếp trong component.
- Tái sử dụng layout/list/filter hiện có khi hợp lý.

Search/RAG:

- Search/RAG tiếp tục dựa trên document/chunk core.
- Module hợp đồng có thể filter theo metadata module bằng API riêng ở giai đoạn sau, nhưng không sửa Qdrant payload nếu chưa cần.
- Citation luôn trỏ về document/chunk/page nguồn.

## Schema Đã Triển Khai

Mục tiêu 2 đã tạo bảng `contract_records` bằng migration `0011_contract_records`.

Các cột chính:

- `id`: UUID primary key.
- `document_id`: liên kết tới `documents.id`.
- `contract_number`.
- `contract_title`.
- `supplier_name`.
- `sign_date`.
- `effective_from`, `effective_to`.
- `contract_value`.
- `currency`.
- `status`.
- `notes`.
- `created_at`, `updated_at`, `deleted_at`.

Indexes:

- `ux_contract_records_document_active`: unique partial index trên `document_id` với điều kiện `deleted_at IS NULL`.
- `ix_contract_records_contract_number_active`.
- `ix_contract_records_supplier_active`.
- `ix_contract_records_status_active`.
- `ix_contract_records_sign_date_active`.
- `ix_contract_records_effective_to_active`.

Ghi chú:

- Bảng chỉ lưu metadata nghiệp vụ, không copy OCR text/chunk.
- Soft delete cho phép giữ lịch sử metadata cũ và tạo bản active mới cho cùng document sau này nếu cần.
- API ở mục tiêu tiếp theo nên query mặc định `deleted_at IS NULL`.

## Hướng Dẫn Cho Mục Tiêu Tiếp Theo

Mục tiêu 3 đã thêm backend module hợp đồng theo `router -> service -> repository`.

Endpoint chính:

- `GET /api/v1/contracts`.
- `GET /api/v1/contracts/{contract_id}`.
- `POST /api/v1/contracts`.
- `PATCH /api/v1/contracts/{contract_id}`.
- `DELETE /api/v1/contracts/{contract_id}`.

Quyền:

- User đăng nhập được list/get/create/update metadata hợp đồng.
- Soft delete metadata hợp đồng yêu cầu admin.

Audit:

- `contract.created`.
- `contract.updated`.
- `contract.deleted`.

Mục tiêu 4 nên thêm frontend module UI theo `page -> composable -> service -> API`, dùng các endpoint trên và không gọi API trực tiếp trong component.

---

## Module Thứ Hai (Phase 7)

Chọn module nghiệp vụ thứ hai cho Phase 7: **Công văn đến/đi**.

## Lý Do Chọn

- Phòng vật tư xử lý hàng ngày công văn đến (yêu cầu, chỉ đạo, phối hợp) và công văn đi (báo cáo, đề xuất, phúc đáp); cần sổ theo dõi metadata nghiệp vụ tách khỏi danh sách document thuần OCR.
- Hệ thống đã có `business_type=incoming_dispatch` / `outgoing_dispatch` trong catalog upload/search và document core đã lưu `document_number`, `issued_date`, `issuing_agency`, `recipient`, `excerpt` từ OCR — module mới tận dụng nền này mà không trùng lặp text/chunk.
- Pattern `contract_records` đã chứng minh: metadata 1-1 với `documents`, CRUD/filter UI, audit log, liên kết hai chiều document detail, search filter theo metadata module.
- Module công văn tạo giá trị ngay cho tra cứu theo số/ký hiệu, đơn vị ban hành, nơi nhận, trạng thái xử lý nội bộ mà document list chưa đủ chuyên biệt.

## Ứng Viên Không Chọn Ở Phase 7

- Quyết định/thông báo: gần document core hơn; chưa cần sổ nghiệp vụ riêng ở MVP này.
- Phiếu/đề xuất vật tư: dễ kéo sang inventory/procurement workflow nhiều bước, vượt scope Phase 7.

## Tên Kỹ Thuật

- Bảng: `dispatch_records`
- Model: `DispatchRecord`
- API prefix: `/api/v1/dispatches`
- Frontend route: `/dispatches`
- Entity audit: `dispatch`

`dispatch` ở đây là tên module nghiệp vụ (công văn đến/đi), không nhầm với HTTP dispatch hay worker queue.

## Scope MVP

MVP chỉ quản lý sổ công văn đến/đi như lớp metadata nghiệp vụ liên kết document core, không thay thế OCR/search/document workflow.

### Metadata Tối Thiểu

| Trường | Mô tả | Ghi chú |
|--------|--------|---------|
| `document_id` | Liên kết 1-1 tới `documents` | Bắt buộc; partial unique index active |
| `dispatch_type` | Loại công văn: `incoming` (đến) hoặc `outgoing` (đi) | Map catalog `incoming_dispatch` / `outgoing_dispatch` |
| `document_number` | Số công văn | Ví dụ `123/CV-VT` |
| `document_symbol` | Ký hiệu | Ví dụ `CV-VT`; optional |
| `issued_date` | Ngày ban hành | Date |
| `issuing_agency` | Đơn vị ban hành | Ví dụ tên phòng/ban/cơ quan gửi |
| `recipient` | Nơi nhận / kính gửi | Text; quan trọng với công văn đi |
| `excerpt` | Trích yếu | Text ngắn, không copy full OCR |
| `status` | Trạng thái xử lý nghiệp vụ module | Xem bảng status bên dưới |
| `notes` | Ghi chú nội bộ | Optional |

Trường bổ sung khi tạo từ document (read-only trong response, không lưu trùng vào bảng module nếu đã có trên `documents`):

- `document_title`, `document_status` — join từ `documents` khi list/get, giống pattern `ContractRead`.

### Trạng Thái MVP (`status`)

| Giá trị | Nhãn UI | Ý nghĩa |
|---------|---------|---------|
| `draft` | Nháp | Metadata chưa chốt |
| `registered` | Đã vào sổ | Đã ghi nhận vào sổ công văn |
| `processing` | Đang xử lý | Đơn vị đang xử lý nội bộ |
| `completed` | Hoàn thành | Đã xử lý xong, không còn tác vụ mở |
| `archived` | Lưu trữ | Đóng hồ sơ, chỉ tra cứu |

Không mở workflow chuyển trạng thái nhiều bước có rule engine; user/admin cập nhật `status` trực tiếp qua form PATCH.

### Workflow MVP

- User đăng nhập upload hoặc chọn document có `business_type` là `incoming_dispatch` hoặc `outgoing_dispatch`.
- Tạo/cập nhật metadata công văn liên kết `document_id`; form có thể pre-fill từ metadata document hiện có (`document_number`, `issued_date`, `issuing_agency`, `recipient`, `excerpt`).
- List/filter theo: `dispatch_type`, số/ký hiệu, ngày ban hành, đơn vị ban hành, nơi nhận, trích yếu (query `q`), trạng thái, `document_id`.
- Detail/link document nguồn, drill-down sang chunks/search dashboard (preset `q`, `document_number` hoặc filter dispatch sau khi search filter module hoàn thiện).
- Audit log cho create/update/delete mềm metadata.

### Không Làm Trong MVP

- Không quản lý inventory, phiếu xuất kho, đề xuất mua sắm hoặc luồng phê duyệt nhiều bước (trình ký, chuyển phòng, hạn xử lý SLA).
- Không tạo bảng file đính kèm riêng — file vẫn nằm ở `document_files` / document core.
- Không tự động trích xuất toàn bộ metadata công văn bằng LLM; chỉ pre-fill từ metadata document/OCR đã có nếu user chọn document nguồn.
- Không denormalize OCR text/chunk vào `dispatch_records` hoặc Qdrant payload ở giai đoạn schema/API MVP.
- Không thêm service ngoài PostgreSQL/Qdrant/Redis hiện có.

## Boundary Kỹ Thuật

### Backend

```text
router -> service -> repository
```

- Module có `dispatches` router, `DispatchService`, `DispatchRepository` riêng.
- Bảng `dispatch_records`: UUID primary key, `created_at`, `updated_at`, `deleted_at`.
- Không hard delete metadata.
- Liên kết document core qua `document_id`; validate document active và chưa có dispatch active khác (1-1 như hợp đồng).
- Validate `dispatch_type` ∈ `{incoming, outgoing}`; khuyến nghị (không bắt buộc hard-fail MVP) khớp `documents.business_type` tương ứng.

### Frontend

```text
page -> composable -> service -> API
```

- Page `/dispatches` dùng `useDispatches` + `dispatch.service.ts`.
- Không gọi API trực tiếp trong component.
- Tái sử dụng layout list/filter/pagination/form từ `/contracts`.

### Search/RAG

- Search/RAG tiếp tục dựa trên document/chunk core.
- Filter search theo metadata dispatch (`dispatch_type`, `document_number`, `issuing_agency`, `status`) là hạng mục sau schema/API/UI MVP, theo pattern contract filter Phase 7 mục tiêu 3 — không bắt buộc trong mục tiêu thiết kế này.
- Citation luôn trỏ về document/chunk/page nguồn.

## Quyền Và Audit

### Quyền

| Hành động | User đăng nhập | Admin |
|-----------|----------------|-------|
| List / get | Có | Có |
| Get by `document_id` | Có | Có |
| Create / update metadata | Có | Có |
| Soft delete | Không (`403`) | Có |

Giữ nhất quán với module hợp đồng: user quản lý metadata hàng ngày; admin xóa mềm khi cần.

### Audit Actions

- `dispatch.created`
- `dispatch.updated`
- `dispatch.deleted`

`entity_type=dispatch`, `entity_id=<dispatch_record.id>`, metadata JSON gọn (ví dụ `dispatch_type`, `document_number`, `status`).

## Schema Đã Triển Khai (Mục Tiêu 5)

Mục tiêu 5 đã tạo bảng `dispatch_records` bằng migration `0013_dispatch_records`.

### Các Cột Chính

- `id`: UUID primary key.
- `document_id`: FK `documents.id`, not null.
- `dispatch_type`: `String(16)`, not null — `incoming` | `outgoing`.
- `document_number`: `String(128)`, nullable.
- `document_symbol`: `String(128)`, nullable.
- `issued_date`: `Date`, nullable.
- `issuing_agency`: `String(255)`, nullable.
- `recipient`: `Text`, nullable.
- `excerpt`: `Text`, nullable.
- `status`: `String(32)`, not null, default `draft`.
- `notes`: `Text`, nullable.
- `created_at`, `updated_at`, `deleted_at`.

### Indexes Dự Kiến

- `ux_dispatch_records_document_active`: unique partial trên `document_id` WHERE `deleted_at IS NULL`.
- `ix_dispatch_records_dispatch_type_active`: (`dispatch_type`, `deleted_at`).
- `ix_dispatch_records_document_number_active`: (`document_number`, `deleted_at`).
- `ix_dispatch_records_issuing_agency_active`: (`issuing_agency`, `deleted_at`).
- `ix_dispatch_records_issued_date_active`: (`issued_date`, `deleted_at`).
- `ix_dispatch_records_status_active`: (`status`, `deleted_at`).

### Quan Hệ Model

- `Document.dispatch_record` — `uselist=False`, tương tự `contract_record`.
- `DispatchRecord.document` — `relationship` back_populates.

## API Đã Triển Khai (Mục Tiêu 6)

Mục tiêu 6 đã thêm backend module theo `router -> service -> repository`.

| Method | Path | Mô tả |
|--------|------|--------|
| `GET` | `/api/v1/dispatches` | List + filter + pagination |
| `GET` | `/api/v1/dispatches/{dispatch_id}` | Chi tiết |
| `GET` | `/api/v1/dispatches/by-document/{document_id}` | Lookup theo document (đặt trước `/{dispatch_id}`) |
| `POST` | `/api/v1/dispatches` | Tạo metadata |
| `PATCH` | `/api/v1/dispatches/{dispatch_id}` | Cập nhật |
| `DELETE` | `/api/v1/dispatches/{dispatch_id}` | Soft delete (admin) |

Filter list tối thiểu: `q`, `document_id`, `dispatch_type`, `document_number`, `issuing_agency`, `status`, `issued_date_from`, `issued_date_to`, `sort_by`, `sort_dir`, `limit`, `offset`.

Response list: `{ items, total, limit, offset }` — pattern `ContractListResponse`.

Lỗi nghiệp vụ: `404` không tìm thấy; `409` trùng dispatch active cho cùng `document_id`; `403` user delete.

## Frontend Dự Kiến (Mục Tiêu 7)

- Route `/dispatches`: bảng list, filter, pagination, form tạo/sửa.
- Query `document_id` / `create=1` để drill-down từ document detail (mục tiêu liên kết sau).
- Link document nguồn, nút "Search trong văn bản" preset dashboard.
- Nav item `Công văn` trong app shell.
- Smoke script: `python -m app.scripts.smoke_dispatch_api` (tái chạy được, cleanup mặc định).

## Hướng Dẫn Cho Mục Tiêu Tiếp Theo (Frontend)

Mục tiêu 7 nên thêm frontend `/dispatches` theo `page -> composable -> service -> API`, dùng các endpoint trên và không gọi API trực tiếp trong component.
