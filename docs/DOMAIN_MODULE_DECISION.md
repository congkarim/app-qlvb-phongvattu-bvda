# Domain Module Decision

Cập nhật lần cuối: 2026-06-08 (Phase 18 mục tiêu 1 — thiết kế line items và materials catalog)

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

## Frontend Đã Triển Khai (Mục Tiêu 7)

Mục tiêu 7 đã thêm page `/dispatches` theo `page -> composable -> service -> API`.

- Route `/dispatches`: bảng list, filter, pagination, form tạo/sửa.
- Query `document_id` / `create=1` để drill-down từ document detail (mục tiêu liên kết sau).
- Link document nguồn, nút "Search trong văn bản" preset dashboard.
- Nav item `Công văn` trong app shell.
- Smoke script: `python -m app.scripts.smoke_dispatch_api` (tái chạy được, cleanup mặc định).

## Hướng Dẫn Cho Mục Tiêu Tiếp Theo (Frontend)

Mục tiêu 7 nên thêm frontend `/dispatches` theo `page -> composable -> service -> API`, dùng các endpoint trên và không gọi API trực tiếp trong component.

---

## Module Thứ Ba (Phase 10)

Chọn module nghiệp vụ thứ ba cho Phase 10: **Quyết định và thông báo**.

## Lý Do Chọn

- Phòng vật tư thường ban hành và lưu trữ quyết định nội bộ (phân công, quy chế vật tư, phê duyệt danh mục) và thông báo (triển khai, hướng dẫn, nhắc việc); cần sổ theo dõi metadata tách khỏi danh sách document thuần OCR.
- Hệ thống đã có `business_type=decision` trong catalog upload/search; OCR classifier nhận diện `QĐ` (Quyết định) và `TB` (Thông báo); chunking nhóm A đã cắt theo `Điều` cho quyết định — module mới tận dụng nền này mà không trùng lặp text/chunk.
- Pattern `contract_records` / `dispatch_records` đã chứng minh: metadata 1-1 với `documents`, CRUD/filter UI, audit log, liên kết hai chiều document detail.
- Module quyết định/thông báo tạo giá trị tra cứu theo số/ký hiệu, đơn vị ban hành, trích yếu, hiệu lực và trạng thái nội bộ mà document list chưa đủ chuyên biệt.

## Ứng Viên Không Chọn Ở Phase 10

- Phiếu/đề xuất vật tư: dễ kéo sang inventory/procurement workflow nhiều bước, vượt scope Phase 10.
- Tách thành hai module riêng (quyết định vs thông báo): trùng metadata và workflow; gộp một module với `decision_kind` đơn giản hơn cho MVP.

## Tên Kỹ Thuật

- Bảng: `decision_records`
- Model: `DecisionRecord`
- API prefix: `/api/v1/decisions`
- Frontend route: `/decisions`
- Entity audit: `decision`

`decision` ở đây là tên module nghiệp vụ (quyết định/thông báo), không nhầm với quyết định kiến trúc hay business rule engine.

## Scope MVP

MVP chỉ quản lý sổ quyết định/thông báo như lớp metadata nghiệp vụ liên kết document core, không thay thế OCR/search/document workflow.

### Metadata Tối Thiểu

| Trường | Mô tả | Ghi chú |
|--------|--------|---------|
| `document_id` | Liên kết 1-1 tới `documents` | Bắt buộc; partial unique index active |
| `decision_kind` | Loại văn bản module: `decision` (quyết định) hoặc `notification` (thông báo) | Map `document_type` OCR `QĐ` / `TB` khi pre-fill |
| `document_number` | Số quyết định/thông báo | Ví dụ `02/QĐ-VT` |
| `document_symbol` | Ký hiệu | Ví dụ `QĐ-VT`; optional |
| `issued_date` | Ngày ban hành | Date |
| `issuing_agency` | Đơn vị ban hành | Ví dụ tên phòng/ban |
| `excerpt` | Trích yếu | Text ngắn, không copy full OCR |
| `effective_from` | Ngày có hiệu lực | Optional; quan trọng với quyết định |
| `effective_to` | Ngày hết hiệu lực | Optional |
| `status` | Trạng thái xử lý nghiệp vụ module | Xem bảng status bên dưới |
| `notes` | Ghi chú nội bộ | Optional |

Trường bổ sung khi tạo từ document (read-only trong response, join từ `documents` — không lưu trùng vào bảng module):

- `document_title`, `document_status`, `document_type` (mã OCR `QĐ`/`TB` nếu có).

Không lưu `recipient`, `signer_name`, `signer_title` trong bảng module MVP — đã có trên `documents` và hiển thị qua document detail; form có thể pre-fill trích yếu/số/ngày từ metadata document.

### Mapping `business_type`

| `decision_kind` | `documents.business_type` khuyến nghị | `documents.document_type` OCR thường gặp |
|-----------------|--------------------------------------|----------------------------------------|
| `decision` | `decision` | `QĐ` |
| `notification` | `decision` | `TB` |

MVP **không** thêm `business_type=notification` vào catalog — cả quyết định và thông báo dùng `business_type=decision`; phân biệt bằng `decision_kind` và/hoặc `document_type`. Validate `decision_kind` ∈ `{decision, notification}`; khuyến nghị (không hard-fail MVP) khớp `document_type` tương ứng khi document đã có classification.

### Trạng Thái MVP (`status`)

| Giá trị | Nhãn UI | Ý nghĩa |
|---------|---------|---------|
| `draft` | Nháp | Metadata chưa chốt |
| `registered` | Đã vào sổ | Đã ghi nhận vào sổ quyết định/thông báo |
| `effective` | Đang hiệu lực | Văn bản đang có hiệu lực thực thi |
| `expired` | Hết hiệu lực | Quá `effective_to` hoặc đánh dấu hết hiệu lực |
| `revoked` | Đã thu hồi | Bãi bỏ/thu hồi nội bộ |
| `archived` | Lưu trữ | Đóng hồ sơ, chỉ tra cứu |

Không mở workflow chuyển trạng thái nhiều bước có rule engine; user/admin cập nhật `status` trực tiếp qua form PATCH.

### Workflow MVP

- User đăng nhập upload hoặc chọn document có `business_type=decision`.
- Tạo/cập nhật metadata quyết định/thông báo liên kết `document_id`; form pre-fill từ metadata document (`document_number`, `issued_date`, `issuing_agency`, `excerpt`, gợi ý `decision_kind` từ `document_type` `QĐ`/`TB`).
- List/filter theo: `decision_kind`, số/ký hiệu, ngày ban hành, đơn vị ban hành, trích yếu (`q`), trạng thái, khoảng `effective_from`/`effective_to`, `document_id`.
- Detail/link document nguồn, drill-down sang chunks/search dashboard (preset `q`, `document_number`).
- Audit log cho create/update/delete mềm metadata.

### Không Làm Trong MVP

- Không quản lý inventory, đề xuất mua sắm, phiếu xuất kho hoặc luồng phê duyệt nhiều bước (trình ký, chuyển phòng, SLA).
- Không tạo bảng file đính kèm riêng — file vẫn nằm ở `document_files` / document core.
- Không tự động trích xuất toàn bộ metadata bằng LLM; chỉ pre-fill từ metadata document/OCR đã có.
- Không denormalize OCR text/chunk vào `decision_records` hoặc Qdrant payload ở giai đoạn schema/API MVP.
- Không thêm `business_type` mới vào catalog admin (ví dụ `notification`) — dùng `decision` + `decision_kind`.
- Không thêm service ngoài PostgreSQL/Qdrant/Redis hiện có.

## Boundary Kỹ Thuật

### Backend

```text
router -> service -> repository
```

- Module có `decisions` router, `DecisionService`, `DecisionRepository` riêng.
- Bảng `decision_records`: UUID primary key, `created_at`, `updated_at`, `deleted_at`.
- Không hard delete metadata.
- Liên kết document core qua `document_id`; validate document active và chưa có decision active khác (1-1 như hợp đồng/công văn).
- Validate `decision_kind` ∈ `{decision, notification}`.

### Frontend

```text
page -> composable -> service -> API
```

- Page `/decisions` dùng `useDecisions` + `decision.service.ts`.
- Không gọi API trực tiếp trong component.
- Tái sử dụng layout list/filter/pagination/form từ `/contracts` và `/dispatches`.

### Search/RAG

- Search/RAG tiếp tục dựa trên document/chunk core; filter `business_type=decision` đã có trên dashboard.
- Filter search theo metadata decision (`decision_kind`, `document_number`, `issuing_agency`, `status`, hiệu lực) là hạng mục sau schema/API/UI MVP — theo pattern contract/dispatch filter Phase 7.
- Citation luôn trỏ về document/chunk/page nguồn; chunking nhóm A (quyết định theo `Điều`) không đổi.

## Quyền Và Audit

### Quyền

| Hành động | User đăng nhập | Admin |
|-----------|----------------|-------|
| List / get | Có | Có |
| Get by `document_id` | Có | Có |
| Create / update metadata | Có | Có |
| Soft delete | Không (`403`) | Có |

Giữ nhất quán với module hợp đồng và công văn: user quản lý metadata hàng ngày; admin xóa mềm khi cần.

### Audit Actions

- `decision.created`
- `decision.updated`
- `decision.deleted`

`entity_type=decision`, `entity_id=<decision_record.id>`, metadata JSON gọn (ví dụ `decision_kind`, `document_number`, `status`).

## Schema Đã Triển Khai (Mục Tiêu 2)

Mục tiêu 2 đã tạo bảng `decision_records` bằng migration `0014_decision_records`.

### Các Cột Chính

- `id`: UUID primary key.
- `document_id`: FK `documents.id`, not null.
- `decision_kind`: `String(16)`, not null — `decision` | `notification`.
- `document_number`: `String(128)`, nullable.
- `document_symbol`: `String(128)`, nullable.
- `issued_date`: `Date`, nullable.
- `issuing_agency`: `String(255)`, nullable.
- `excerpt`: `Text`, nullable.
- `effective_from`: `Date`, nullable.
- `effective_to`: `Date`, nullable.
- `status`: `String(32)`, not null, default `draft`.
- `notes`: `Text`, nullable.
- `created_at`, `updated_at`, `deleted_at`.

### Indexes

- `ux_decision_records_document_active`: unique partial trên `document_id` WHERE `deleted_at IS NULL`.
- `ix_decision_records_decision_kind_active`: (`decision_kind`, `deleted_at`).
- `ix_decision_records_document_number_active`: (`document_number`, `deleted_at`).
- `ix_decision_records_issuing_agency_active`: (`issuing_agency`, `deleted_at`).
- `ix_decision_records_issued_date_active`: (`issued_date`, `deleted_at`).
- `ix_decision_records_effective_from_active`: (`effective_from`, `deleted_at`).
- `ix_decision_records_effective_to_active`: (`effective_to`, `deleted_at`).
- `ix_decision_records_status_active`: (`status`, `deleted_at`).

### Quan Hệ Model

- `Document.decision_record` — `uselist=False`, tương tự `contract_record` / `dispatch_record`.
- `DecisionRecord.document` — `relationship` back_populates.

## API Đã Triển Khai (Mục Tiêu 3)

Mục tiêu 3 đã thêm backend module theo `router -> service -> repository`.

| Method | Path | Mô tả |
|--------|------|--------|
| `GET` | `/api/v1/decisions` | List + filter + pagination |
| `GET` | `/api/v1/decisions/{decision_id}` | Chi tiết |
| `GET` | `/api/v1/decisions/by-document/{document_id}` | Lookup theo document (đặt trước `/{decision_id}`) |
| `POST` | `/api/v1/decisions` | Tạo metadata |
| `PATCH` | `/api/v1/decisions/{decision_id}` | Cập nhật |
| `DELETE` | `/api/v1/decisions/{decision_id}` | Soft delete (admin) |

Filter list tối thiểu: `q`, `document_id`, `decision_kind`, `document_number`, `issuing_agency`, `status`, `issued_date_from`, `issued_date_to`, `effective_from`, `effective_to`, `sort_by`, `sort_dir`, `limit`, `offset`.

Response list: `{ items, total, limit, offset }` — pattern `DispatchListResponse` / `ContractListResponse`.

Lỗi nghiệp vụ: `404` không tìm thấy; `409` trùng decision active cho cùng `document_id`; `403` user delete.

Smoke script đề xuất: `python -m app.scripts.smoke_decision_api`.

## Frontend Đã Triển Khai (Mục Tiêu 4)

Mục tiêu 4 đã thêm page `/decisions` theo `page -> composable -> service -> API`.

- Route `/decisions`: bảng list, filter, pagination, form tạo/sửa.
- Query `document_id` / `create=1` để drill-down từ document detail.
- Link document nguồn, nút "Search trong văn bản" preset dashboard.
- Nav item `Quyết định` (hoặc `Quyết định & TB`) trong app shell.
- Card trên `/documents/[id]` liên kết hai chiều với module decision khi document có metadata module.

## Hướng Dẫn Cho Phase Sau

Search filter dashboard theo metadata decision (`decision_kind`, hiệu lực, trạng thái) có thể làm theo pattern contract filter Phase 7 — không bắt buộc trong Phase 10.

---

## Thiết Kế Search Filter Dispatch/Decision (Draft — Phase 11 Mục Tiêu 1)

Cập nhật: 2026-06-07. Chưa triển khai code; bám pattern contract filter Phase 7.

### Nguyên Tắc

- Search/RAG vẫn retrieval trên document/chunk core + Qdrant vector.
- **Không** sửa Qdrant payload, **không** re-index chunk.
- Filter metadata module: pre-resolve danh sách `document_id` từ PostgreSQL (`dispatch_records`, `decision_records`) trước khi lọc hit vector/keyword — giống `contract_records`.
- Citation vẫn trỏ `document_id` + `chunk_id`; enrich metadata module chỉ để hiển thị dashboard.

### Tham Số API (`POST /search/semantic`, `POST /search/answer`)

| Tham số | Module | Repository param | Match logic (giống list API) |
|---------|--------|------------------|------------------------------|
| `dispatch_type` | Dispatch | `dispatch_type` | Exact `incoming` \| `outgoing` |
| `dispatch_status` | Dispatch | `status` | Exact enum MVP |
| `decision_kind` | Decision | `decision_kind` | Exact `decision` \| `notification` |
| `decision_status` | Decision | `status` | Exact enum MVP |
| `effective_from` | Decision | `effective_from` | `decision_records.effective_from >= value` |
| `effective_to` | Decision | `effective_to` | `decision_records.effective_to <= value` |
| `document_number` | Dispatch + Decision + document core | `document_number` | `ilike %value%` trên bảng module; đồng thời filter Qdrant/document khi có giá trị |
| `issuing_agency` | Dispatch + Decision + document core | `issuing_agency` | `ilike %value%` — **field mới** trên search request |

Field contract hiện có (`contract_number`, `supplier_name`, `contract_status`) giữ nguyên, không đổi semantics.

### Pre-Resolve Và Giao `document_id`

1. Mỗi nhóm module có helper `_resolve_*_document_ids()` → `None` (không filter) hoặc `set[str]`.
2. Nhóm active khi có ít nhất một tham số “kích hoạt” (xem bảng trong `PROJECT_STATUS.md` Phase 11 mục tiêu 1).
3. Nhiều nhóm active → **intersection** các set; set rỗng ở bất kỳ nhóm nào → trả `[]` sớm.
4. `document_number` / `issuing_agency` chỉ thắt chặt repo module khi nhóm đó đã active (không tự kích hoạt nhóm).

### Repository (Mục Tiêu 2)

```text
DispatchRepository.list_document_ids_by_metadata(
  dispatch_type?, document_number?, issuing_agency?, status?  # status từ dispatch_status API
)
DecisionRepository.list_document_ids_by_metadata(
  decision_kind?, document_number?, issuing_agency?, status?, effective_from?, effective_to?
)
```

Chỉ bản ghi `deleted_at IS NULL`; join `documents` active. Filter rỗng → không giới hạn (caller quyết định có gọi hay không).

### Enrich Response (Mục Tiêu 3)

`SemanticSearchResult` bổ sung (nullable khi không có bản ghi module active):

- Dispatch: `dispatch_id`, `dispatch_type`, `dispatch_status`
- Decision: `decision_id`, `decision_kind`, `decision_status`, `effective_from`, `effective_to`

### Frontend Dashboard (Mục Tiêu 4–5)

- `SemanticSearchFilters` / `RagAnswerFilters`: thêm cột tương ứng bảng API.
- `normalizeSearchPayload()`: map `dispatch_status` → API, không gửi field rỗng.
- `dashboard.vue`: hiện nhóm filter dispatch/decision có điều kiện theo `business_type`; preset đọc route query khi mount.
- Preset từ module pages (pattern `/contracts`):
  - `/dispatches`: `q`, `document_number`, `dispatch_type`, `dispatch_status`, `business_type`
  - `/decisions`: `q`, `document_number`, `business_type=decision`, `decision_kind`, `decision_status`

### Không Làm (Phase 11)

- Không đổi Qdrant collection schema / worker upsert.
- Không LLM; RAG extractive giữ nguyên.
- Không deep-link citation `#chunk-{id}` (Phase 12).

### Search Filter Đã Triển Khai

Cập nhật: 2026-06-07 (Phase 11 hoàn thành).

**Backend** (`POST /api/v1/search/semantic`, `POST /api/v1/search/answer`):

- Pre-resolve `document_id` từ `dispatch_records` / `decision_records` (không sửa Qdrant payload).
- Tham số: `dispatch_type`, `dispatch_status`, `decision_kind`, `decision_status`, `effective_from`, `effective_to`, tái dùng `document_number` / `issuing_agency`.
- Enrich `SemanticSearchResult`: `dispatch_id`, `dispatch_type`, `dispatch_status`, `decision_id`, `decision_kind`, `decision_status`, `effective_from`, `effective_to`.
- Smoke: `python -m app.scripts.smoke_search_module_filters`.

**Frontend dashboard**:

- Filter conditional theo `business_type`; RAG dùng chung bộ lọc semantic search.
- Preset route query khi mount: `q`, `document_number`, `issuing_agency`, `business_type`, `dispatch_type`, `dispatch_status`, `decision_kind`, `decision_status`, `effective_from`, `effective_to`.

**Preset từ module pages** (nút "Search trong văn bản"):

| Trang | Query truyền sang `/dashboard` |
|-------|--------------------------------|
| `/dispatches` | `q`, `document_number`, `issuing_agency`, `dispatch_type`, `dispatch_status`, `business_type` (`incoming_dispatch` / `outgoing_dispatch`) |
| `/decisions` | `q`, `document_number`, `issuing_agency`, `business_type=decision`, `decision_kind`, `decision_status`, `effective_from`, `effective_to` |
| `/contracts` | `q`, `document_number` (giữ pattern hiện có) |

---

## Module Thứ Tư (Phase 13)

Chọn module nghiệp vụ thứ tư cho Phase 13: **Đề xuất / kế hoạch mua sắm vật tư** (và biên bản nghiệm thu đơn giản).

## Lý Do Chọn

- Phòng vật tư cần sổ theo dõi đề xuất mua sắm, kế hoạch/dự toán vật tư và biên bản nghiệm thu gắn với hồ sơ văn bản (công văn đề xuất, kế hoạch nội bộ, biên bản) — metadata chuyên biệt mà document list thuần OCR chưa đủ.
- Pattern `contract_records` / `dispatch_records` / `decision_records` đã chứng minh: metadata 1-1 với `documents`, CRUD/filter UI, audit log, liên kết hai chiều document detail, search filter module (Phase 11).
- Benchmark search đã có fixture `procurement_plan` (kế hoạch mua sắm vật tư) — có thể nối vào smoke procurement/search ở mục tiêu 6.
- Scope giữ **metadata layer** quanh document core; **không** mở inventory, tồn kho, phiếu xuất/nhập hay workflow phê duyệt nhiều bước.

## Ứng Viên Không Chọn Ở Phase 13

- Tách module inventory/tồn kho: vượt scope MVP, dễ kéo sang ERP nhẹ.
- Tách ba module riêng (đề xuất / kế hoạch / nghiệm thu): trùng metadata và workflow; gộp một module với `procurement_kind` đơn giản hơn cho MVP.
- Dùng `business_type=incoming_dispatch` cho mọi hồ sơ procurement: benchmark fixture hiện tạm dùng giá trị này; module mới sẽ chuẩn hóa `business_type=procurement` + `procurement_kind`.

## Tên Kỹ Thuật

- Bảng: `procurement_records`
- Model: `ProcurementRecord`
- API prefix: `/api/v1/procurements`
- Frontend route: `/procurements`
- Entity audit: `procurement`

`procurement` ở đây là tên module nghiệp vụ (đề xuất/kế hoạch mua sắm), không nhầm với quy trình mua sắm đầy đủ hay hệ thống đấu thầu.

## Scope MVP

MVP chỉ quản lý sổ đề xuất/kế hoạch/nghiệm thu như lớp metadata nghiệp vụ liên kết document core, không thay thế OCR/search/document workflow.

### Metadata Tối Thiểu

| Trường | Mô tả | Ghi chú |
|--------|--------|---------|
| `document_id` | Liên kết 1-1 tới `documents` | Bắt buộc; partial unique index active |
| `procurement_kind` | Loại hồ sơ module | `proposal` \| `plan` \| `acceptance` — xem bảng mapping |
| `reference_number` | Số đề xuất / kế hoạch / biên bản | Ví dụ `DX-12/VT`, `KH-42/VT`; nullable nhưng khuyến nghị nhập |
| `title_summary` | Trích yếu / tên hồ sơ nghiệp vụ | Text ngắn; mặc định lấy `documents.title` nếu chưa nhập |
| `requesting_unit` | Đơn vị đề xuất / yêu cầu | Ví dụ tên phòng/ban; có thể pre-fill từ `issuing_agency` |
| `estimated_value` | Giá trị dự kiến / dự toán | `Numeric(18,2)`, nullable |
| `currency` | Đơn vị tiền | Mặc định `VND` |
| `requested_date` | Ngày lập đề xuất / kế hoạch | Date; có thể pre-fill từ `issued_date` |
| `status` | Trạng thái xử lý nghiệp vụ module | Xem bảng status bên dưới |
| `notes` | Ghi chú nội bộ | Optional |

Trường bổ sung khi tạo từ document (read-only trong response, join từ `documents` — không lưu trùng vào bảng module):

- `document_title`, `document_status`, `document_number`, `issued_date`, `issuing_agency`, `excerpt` (hiển thị/pre-fill form; `document_number` có thể gợi ý `reference_number`).

### `procurement_kind`

| Giá trị | Nhãn UI | Ý nghĩa |
|---------|---------|---------|
| `proposal` | Đề xuất mua sắm | Phiếu/tờ trình đề xuất vật tư, dự trù |
| `plan` | Kế hoạch / dự toán | Kế hoạch mua sắm, dự toán vật tư theo kỳ |
| `acceptance` | Biên bản nghiệm thu | Biên bản nghiệm thu hàng hóa/dịch vụ đơn giản (metadata, không line items) |

Validate `procurement_kind` ∈ `{proposal, plan, acceptance}`.

### Mapping `business_type`

| `procurement_kind` | `documents.business_type` khuyến nghị | `documents.document_type` OCR thường gặp |
|--------------------|--------------------------------------|------------------------------------------|
| `proposal` | `procurement` | `ĐX`, `CV` (công văn đề xuất) |
| `plan` | `procurement` | `KH` (kế hoạch) |
| `acceptance` | `procurement` | `BB` (biên bản), `BBNT` |

**Catalog admin:** thêm một mã `business_type=procurement` (nhãn ví dụ "Đề xuất / kế hoạch mua sắm") trong migration hoặc seed đi kèm mục tiêu 2 — **không** thêm `purchase_plan` / `proposal` riêng vào catalog; phân biệt bằng `procurement_kind` (giống `decision` + `decision_kind`).

Khuyến nghị (không hard-fail MVP): khi tạo procurement từ document, `documents.business_type` nên là `procurement`; nếu document cũ còn `incoming_dispatch`/`outgoing_dispatch` vẫn cho phép tạo metadata nhưng UI có thể gợi ý đổi `business_type` trên document.

### Trạng Thái MVP (`status`)

| Giá trị | Nhãn UI | Ý nghĩa |
|---------|---------|---------|
| `draft` | Nháp | Metadata chưa chốt |
| `submitted` | Đã trình | Đã gửi/trình nội bộ |
| `approved` | Đã duyệt | Được phê duyệt (ghi nhận, không mô phỏng workflow trình ký) |
| `rejected` | Từ chối | Không duyệt / trả lại |
| `completed` | Hoàn thành | Đã thực hiện xong (mua sắm/nghiệm thu hoàn tất theo hồ sơ) |
| `archived` | Lưu trữ | Đóng hồ sơ, chỉ tra cứu |

Không mở workflow chuyển trạng thái nhiều bước có rule engine; user/admin cập nhật `status` trực tiếp qua form PATCH.

### Workflow MVP

- User đăng nhập upload hoặc chọn document có `business_type=procurement` (hoặc document đã searchable khác loại nếu cần backfill).
- Tạo/cập nhật metadata procurement liên kết `document_id`; form pre-fill từ metadata document (`document_number` → `reference_number`, `title` → `title_summary`, `issuing_agency` → `requesting_unit`, `issued_date` → `requested_date`, `excerpt` → gợi ý `title_summary`).
- List/filter theo: `procurement_kind`, `reference_number`, `requesting_unit`, trích yếu (`q`), trạng thái, khoảng `requested_date`, `document_id`.
- Detail/link document nguồn, drill-down sang chunks/search dashboard (preset `q`, `reference_number`, `business_type=procurement`; filter procurement đầy đủ ở mục tiêu 6 tùy chọn).
- Audit log cho create/update/delete mềm metadata.

### Không Làm Trong MVP

- Không quản lý tồn kho, phiếu xuất/nhập kho, tồn tối thiểu, đối soát tồn.
- Không workflow trình ký nhiều bước, SLA, assignee, comment thread, luồng phê duyệt có rule.
- Không bảng dòng hàng vật tư chi tiết (line items), đơn giá từng mặt hàng, nhà cung cấp trên từng dòng.
- Không tạo bảng file đính kèm riêng — file vẫn ở `document_files` / document core.
- Không tự động trích xuất toàn bộ metadata bằng LLM; chỉ pre-fill từ metadata document/OCR đã có.
- Không denormalize OCR text/chunk vào `procurement_records` hoặc Qdrant payload ở giai đoạn schema/API MVP.
- Không thêm service ngoài PostgreSQL/Qdrant/Redis hiện có.

## Boundary Kỹ Thuật

### Backend

```text
router -> service -> repository
```

- Module có `procurements` router, `ProcurementService`, `ProcurementRepository` riêng.
- Bảng `procurement_records`: UUID primary key, `created_at`, `updated_at`, `deleted_at`.
- Không hard delete metadata.
- Liên kết document core qua `document_id`; validate document active và chưa có procurement active khác (1-1 như các module trước).
- Validate `procurement_kind` ∈ `{proposal, plan, acceptance}`; `currency` default `VND`; `estimated_value` ≥ 0 nếu có.

### Frontend

```text
page -> composable -> service -> API
```

- Page `/procurements` dùng `useProcurements` + `procurement.service.ts`.
- Không gọi API trực tiếp trong component.
- Tái sử dụng layout list/filter/pagination/form từ `/contracts`, `/dispatches`, `/decisions`.

### Search/RAG

- Search/RAG tiếp tục dựa trên document/chunk core.
- Filter search theo metadata procurement (`procurement_kind`, `reference_number`, `requesting_unit`, `status`) đã triển khai theo pattern Phase 11 pre-resolve `document_id` từ `procurement_records`.
- Citation/deep link `#chunk-{id}` giữ nguyên (Phase 12); enrich response thêm `procurement_id`, `procurement_kind`, `procurement_status`, `reference_number`, `requesting_unit`.
- Benchmark fixture `procurement_plan`: `business_type=procurement` (mục tiêu 6).

## Quyền Và Audit

### Quyền

| Hành động | User đăng nhập | Admin |
|-----------|----------------|-------|
| List / get | Có | Có |
| Get by `document_id` | Có | Có |
| Create / update metadata | Có | Có |
| Soft delete | Không (`403`) | Có |

Giữ nhất quán với module hợp đồng, công văn và quyết định.

### Audit Actions

- `procurement.created`
- `procurement.updated`
- `procurement.deleted`

`entity_type=procurement`, `entity_id=<procurement_record.id>`, metadata JSON gọn (ví dụ `procurement_kind`, `reference_number`, `status`).

## Schema Đã Triển Khai (Mục Tiêu 2)

Migration `0015_procurement_records` (kèm seed catalog `business_type=procurement`).

### Các Cột Chính

- `id`: UUID primary key.
- `document_id`: FK `documents.id`, not null.
- `procurement_kind`: `String(16)`, not null — `proposal` | `plan` | `acceptance`.
- `reference_number`: `String(128)`, nullable.
- `title_summary`: `Text`, nullable.
- `requesting_unit`: `String(255)`, nullable.
- `estimated_value`: `Numeric(18, 2)`, nullable.
- `currency`: `String(8)`, not null, default `VND`.
- `requested_date`: `Date`, nullable.
- `status`: `String(32)`, not null, default `draft`.
- `notes`: `Text`, nullable.
- `created_at`, `updated_at`, `deleted_at`.

### Indexes Dự Kiến

- `ux_procurement_records_document_active`: unique partial trên `document_id` WHERE `deleted_at IS NULL`.
- `ix_procurement_records_procurement_kind_active`: (`procurement_kind`, `deleted_at`).
- `ix_procurement_records_reference_number_active`: (`reference_number`, `deleted_at`).
- `ix_procurement_records_requesting_unit_active`: (`requesting_unit`, `deleted_at`).
- `ix_procurement_records_status_active`: (`status`, `deleted_at`).
- `ix_procurement_records_requested_date_active`: (`requested_date`, `deleted_at`).

### Quan Hệ Model

- `Document.procurement_record` — `uselist=False`, tương tự `contract_record` / `dispatch_record` / `decision_record`.
- `ProcurementRecord.document` — `relationship` back_populates.

## API Đã Triển Khai (Mục Tiêu 3)

| Method | Path | Mô tả |
|--------|------|--------|
| `GET` | `/api/v1/procurements` | List + filter + pagination |
| `GET` | `/api/v1/procurements/{procurement_id}` | Chi tiết |
| `GET` | `/api/v1/procurements/by-document/{document_id}` | Lookup theo document (đặt trước `/{procurement_id}`) |
| `POST` | `/api/v1/procurements` | Tạo metadata |
| `PATCH` | `/api/v1/procurements/{procurement_id}` | Cập nhật |
| `DELETE` | `/api/v1/procurements/{procurement_id}` | Soft delete (admin) |

Filter list tối thiểu: `q`, `document_id`, `procurement_kind`, `reference_number`, `requesting_unit`, `status`, `requested_date_from`, `requested_date_to`, `sort_by`, `sort_dir`, `limit`, `offset`.

`sort_by` khuyến nghị: `requested_date`, `reference_number`, `status`, `created_at`, `updated_at`.

Response list: `{ items, total, limit, offset }` — pattern `DecisionListResponse`.

Lỗi nghiệp vụ: `404` không tìm thấy; `409` trùng procurement active cho cùng `document_id`; `403` user delete.

Smoke script đề xuất: `python -m app.scripts.smoke_procurement_api`.

## Frontend Đã Triển Khai (Mục Tiêu 4)

- Route `/procurements`: bảng list, filter, pagination, form tạo/sửa — hoàn thành mục tiêu 4.
- Query `document_id` / `create=1` hỗ trợ drill-down từ document detail (mục tiêu 5).
- Nav item `Mua sắm` trong app shell.
- Nút "Search trong văn bản" preset dashboard (`business_type=procurement`).

## Frontend Đã Triển Khai (Mục Tiêu 5)

- Card **Mua sắm** trên `/documents/[id]`: metadata, "Mở Mua sắm", "Search trong văn bản", "Tạo metadata mua sắm".
- Liên kết ngược `/procurements` → document detail + preset dashboard (mục tiêu 4).

## Search Filter Procurement (Đã Triển Khai — Mục Tiêu 6)

Bám pattern Phase 11; triển khai 2026-06-07.

### Tham Số API (`POST /search/semantic`, `POST /search/answer`)

| Tham số | Repository param | Match logic |
|---------|------------------|-------------|
| `procurement_kind` | `procurement_kind` | Exact `proposal` \| `plan` \| `acceptance` |
| `procurement_status` | `status` | Exact enum MVP |
| `reference_number` | `reference_number` | `ilike %value%` (khi nhóm procurement active) |
| `requesting_unit` | `requesting_unit` | `ilike %value%` |

`ProcurementRepository.list_document_ids_by_metadata(...)` — chỉ `deleted_at IS NULL`; intersection với contract/dispatch/decision filter groups nếu nhiều nhóm active.

Enrich `SemanticSearchResult` (nullable): `procurement_id`, `procurement_kind`, `procurement_status`, `reference_number`, `requesting_unit`.

Preset từ `/procurements` sang `/dashboard`: `q`, `reference_number`, `requesting_unit`, `business_type=procurement`, `procurement_kind`, `procurement_status`.

## Module Onboarding Sau OCR (Phase 14 — Mục Tiêu 1)

Trạng thái: thiết kế đã chốt (2026-06-07); triển khai code từ mục tiêu 2.

### Mục Tiêu Nghiệp Vụ

Sau OCR/searchable, hệ thống **gợi ý** (không tự tạo im lặng):

1. `documents.business_type` phù hợp catalog admin.
2. Module đích (`contract` | `dispatch` | `decision` | `procurement`) và field pre-fill cho form CRUD module.
3. CTA trên document detail và filter list “thiếu metadata module”.

Nguồn dữ liệu: `DocumentClassifierService` (rule-based, đã chạy trong worker) + metadata document đã lưu (`document_type`, `classification_confidence`, `document_number`, `issuing_agency`, `excerpt`, `recipient`, `issued_date`, …).

Không dùng LLM. Không auto-create `*_records` — user xác nhận qua form/API CRUD hiện có.

### Catalog `business_type` (Migration `0012` + `0015`)

| Code | Nhãn catalog | Module liên kết |
|------|--------------|-----------------|
| `incoming_dispatch` | Công văn đến | `dispatch` (`dispatch_type=incoming`) |
| `outgoing_dispatch` | Công văn đi | `dispatch` (`dispatch_type=outgoing`) |
| `contract` | Hợp đồng | `contract` |
| `decision` | Quyết định | `decision` (`decision_kind` phân nhánh) |
| `procurement` | Đề xuất / kế hoạch mua sắm | `procurement` (`procurement_kind` phân nhánh) |

Frontend lấy option từ Catalog API (`useCatalogs`); không hardcode danh sách trên UI onboarding.

### Bảng Mapping `document_type` → Module

`document_type` là nhãn classifier (`DocumentClassifierService` / skill `vn-admin-doc-ocr-classifier`). Cột **confidence base** là điểm gợi ý module trước khi cộng/trừ heuristic; service onboarding lấy `min(confidence base, classification_confidence)` làm `module_confidence`.

| `document_type` | `target_module` | `suggested_business_type` | Sub-kind | Confidence base | Ghi chú |
|-----------------|-----------------|---------------------------|----------|-----------------|---------|
| `HĐ` | `contract` | `contract` | — | 0.90 | Hợp đồng |
| `BGN`, `BTT` | `contract` | `contract` | — | 0.82 | Bản ghi nhớ / thỏa thuận — gần hợp đồng, confidence thấp hơn |
| `CV`, `CĐ` | `dispatch` | *heuristic* | `dispatch_type` | 0.90 | Xem mục heuristic CV bên dưới |
| `PG`, `PC`, `PB`, `TCg` | `dispatch` | `incoming_dispatch` | `incoming` | 0.78 | Phiếu gửi/chuyển/báo — mặc định đến, cần xác nhận |
| `QĐ` | `decision` | `decision` | `decision` | 0.94 | Quyết định |
| `TB` | `decision` | `decision` | `notification` | 0.93 | Thông báo |
| `NQ` | `decision` | `decision` | `decision` | 0.80 | Nghị quyết cá biệt — gợi ý yếu hơn QĐ |
| `KH` | `procurement` | `procurement` | `plan` | 0.90 | Kế hoạch |
| `TTr` | `procurement` | `procurement` | `proposal` | 0.91 | Tờ trình đề xuất |
| `BB` | `procurement` | `procurement` | `acceptance` | 0.92 | Biên bản nghiệm thu |
| `BC`, `PA`, `ĐA`, `DA`, `CTr` | `procurement` | `procurement` | `proposal` | 0.72 | Báo cáo/phương án/đề án — gợi ý yếu, thường `needs_metadata_review` |
| `CT`, `QC`, `QYĐ`, `TC`, `HD`, `GM`, `GGT`, `GUQ`, `GNP` | — | — | — | — | **Không** gợi ý module Phase 14; có thể chỉ nhắc review metadata document |
| `UNKNOWN` | — | — | — | ≤0.45 | Không gợi ý module; nhắc review OCR/metadata |

Nếu `documents.business_type` đã khớp một module (ví dụ `contract`) nhưng `document_type` map sang module khác → **ưu tiên `business_type` đã có** cho `target_module`; ghi `reasons[]` cảnh báo lệch loại, không ép đổi business_type tự động.

### Heuristic `CV` / `CĐ` → `incoming_dispatch` vs `outgoing_dispatch`

Áp dụng khi `document_type` ∈ `{CV, CĐ}` và upload **chưa** chọn `business_type` (hoặc đang gợi ý đổi từ rỗng):

1. **Outgoing** (`outgoing_dispatch`, `dispatch_type=outgoing`) nếu `excerpt` khớp `^V/v\s` (công văn đi “V/v …”).
2. **Incoming** (`incoming_dispatch`, `dispatch_type=incoming`) nếu **một trong**:
   - `document_type=CĐ` (công điện thường đến).
   - `excerpt` có `Kính gửi` (khi còn lưu trên document).
   - Có `recipient` (classifier đã trích từ khối Kính gửi) và excerpt **không** bắt đầu bằng `V/v`.
3. **Mặc định khi mơ hồ:** `incoming_dispatch`, `dispatch_type=incoming`, cap `module_confidence` ≤ **0.75**, `reasons` += `dispatch_direction_ambiguous`.

Khi user đã chọn `incoming_dispatch` / `outgoing_dispatch` lúc upload → dùng giá trị đó, map `dispatch_type` tương ứng, không chạy heuristic hướng.

### Ngưỡng Confidence Và Trạng Thái UI

| Ngưỡng | Điều kiện | Hành vi |
|--------|-----------|---------|
| **High** | `module_confidence` ≥ **0.85** | Banner gợi ý nổi bật; đủ điều kiện worker **audit** gợi ý `business_type` (mục tiêu 3) |
| **Medium** | **0.70** ≤ confidence &lt; 0.85 | Hiển thị gợi ý kèm nhãn “cần xác nhận”; không auto-apply business_type trên worker |
| **Low** | &lt; 0.70 hoặc `document_type=UNKNOWN` | Không gợi ý tạo module; chỉ nhắc review metadata document (`needs_metadata_review=true`) |

`module_confidence = min(mapping_confidence_base, document.classification_confidence hoặc 1.0 nếu null)`.

### Guard Manual Review Và Upload

Không gợi ý áp dụng / không worker auto-suggest khi:

- `documents.metadata_reviewed_at IS NOT NULL`, hoặc
- `documents.metadata_source IN ('manual', 'mixed')`.

Upload đã chọn `business_type` không rỗng → **không đổi** `business_type` trong worker; onboarding API vẫn có thể gợi ý **module pre-fill** nếu thiếu bản ghi active và `business_type` map được module.

API `onboarding-suggestions` trả `eligible=false` + `block_reason` khi:

| `block_reason` | Ý nghĩa |
|----------------|---------|
| `not_searchable` | `documents.status` chưa `searchable` |
| `module_exists` | Đã có bản ghi module active 1-1 |
| `manual_metadata` | Metadata document đã review thủ công |
| `unmapped_document_type` | `document_type` không map module |
| `low_confidence` | Dưới ngưỡng medium |

### Map Field Classifier / Document → Form Module

Nguồn: kết quả classify (đã persist lên `documents`) + `documents.title`. Field null thì bỏ qua trong `suggested_module_fields`.

**Contract** (`ContractCreateRequest`):

| Field module | Nguồn gợi ý |
|--------------|---------------|
| `document_id` | `documents.id` |
| `contract_number` | `document_number` hoặc `document_symbol` |
| `contract_title` | `title` hoặc `excerpt` hoặc `documents.title` |
| `sign_date` | `issued_date` |
| `currency` | `"VND"` |
| `status` | `"draft"` |

**Dispatch** (`DispatchCreateRequest`):

| Field module | Nguồn gợi ý |
|--------------|---------------|
| `document_id` | `documents.id` |
| `dispatch_type` | heuristic hoặc từ `business_type` hiện có |
| `document_number` | `document_number` |
| `document_symbol` | `document_symbol` |
| `issued_date` | `issued_date` |
| `issuing_agency` | `issuing_agency` hoặc `agency_name` từ classify |
| `recipient` | `recipient` |
| `excerpt` | `excerpt` |
| `status` | `"draft"` |

**Decision** (`DecisionCreateRequest`):

| Field module | Nguồn gợi ý |
|--------------|---------------|
| `document_id` | `documents.id` |
| `decision_kind` | từ bảng mapping (`QĐ`→`decision`, `TB`→`notification`) |
| `document_number` | `document_number` |
| `document_symbol` | `document_symbol` |
| `issued_date` | `issued_date` |
| `issuing_agency` | `issuing_agency` |
| `excerpt` | `excerpt` |
| `effective_from` | `issued_date` (gợi ý mặc định MVP) |
| `status` | `"draft"` |

**Procurement** (`ProcurementCreateRequest`):

| Field module | Nguồn gợi ý |
|--------------|---------------|
| `document_id` | `documents.id` |
| `procurement_kind` | từ bảng mapping (`KH`→`plan`, `TTr`→`proposal`, `BB`→`acceptance`, …) |
| `reference_number` | `document_number` |
| `title_summary` | `excerpt` hoặc `title` hoặc `documents.title` |
| `requesting_unit` | `issuing_agency` |
| `requested_date` | `issued_date` |
| `currency` | `"VND"` |
| `status` | `"draft"` |

Form UI hiện tại (`/contracts`, `/dispatches`, `/decisions`, `/procurements`) với `?document_id=&create=1` **chỉ** set `form.document_id` — mục tiêu 4 sẽ truyền thêm query/body pre-fill từ `suggested_module_fields` hoặc hydrate từ API onboarding trước khi hiển thị form.

### API `GET /api/v1/documents/{document_id}/onboarding-suggestions` (Mục Tiêu 2)

Read-only. Router `documents` → `ModuleOnboardingService` (service mới; có thể delegate mapping tới helper dùng chung với worker).

Response shape (Pydantic):

```json
{
  "document_id": "uuid",
  "eligible": true,
  "block_reason": null,
  "needs_metadata_review": false,
  "suggested_business_type": "contract",
  "business_type_confidence": 0.9,
  "target_module": "contract",
  "module_confidence": 0.9,
  "module_kind": null,
  "reasons": ["document_type=HĐ", "mapping_contract"],
  "suggested_module_fields": {
    "contract_number": "01/HĐ-2026",
    "contract_title": "HỢP ĐỒNG MUA SẮM VẬT TƯ",
    "sign_date": "2026-06-07",
    "currency": "VND",
    "status": "draft"
  }
}
```

- `target_module`: `contract` | `dispatch` | `decision` | `procurement` | `null`.
- `module_kind`: sub-kind tùy module — `dispatch_type`, `decision_kind`, hoặc `procurement_kind` (string enum hiện có); `null` với contract.
- `suggested_module_fields`: object flat, key trùng field `*CreateRequest`; **không** gồm `document_id` (client đã biết).

Endpoint áp dụng `business_type` (mục tiêu 4): dùng `PATCH /api/v1/documents/{id}` hiện có; sau apply set `metadata_source=mixed` nếu trước đó là `auto`, và audit `document.business_type_applied`.

### Worker / Audit (Mục Tiêu 3)

Trong `_extract_and_store_metadata` sau classify (đã triển khai mục tiêu 3):

- Nếu upload **không** chọn `business_type` (null/empty) và không manual guard → audit `document.onboarding_suggested` với payload gợi ý (`applied=false`); **không** đổi `business_type` trên document (audit-only).
- Nếu upload đã chọn `business_type` → không ghi audit onboarding; worker vẫn giữ `business_type` như cũ khi auto-extract metadata.
- Tùy chọn sau MVP: auto-set `business_type` + `metadata_source=mixed` khi `module_confidence` ≥ 0.85; Phase 14 mặc định **audit-only**.

Audit actions:

| Action | Khi nào |
|--------|---------|
| `document.onboarding_suggested` | Sau OCR, có gợi ý module hợp lệ |
| `document.business_type_applied` | User/UI PATCH áp dụng `suggested_business_type` |

### Frontend UX (Mục Tiêu 4–5)

**Document detail** (`/documents/[id]`):

- Gọi onboarding API khi `status=searchable` và chưa có card module active.
- Banner **Gợi ý metadata**: hiển thị `suggested_business_type`, `target_module`, confidence; nút **Áp dụng loại nghiệp vụ** (PATCH document); nút **Tạo metadata {module}** → `/contracts|dispatches|decisions|procurements?document_id=&create=1` kèm pre-fill (query serialized hoặc fetch lại API trên trang module).
- Low confidence: `Message` severity warn, không ẩn workflow.

**Document list** (mục tiêu 5):

- Query `missing_module_metadata=true` trên list documents API.
- Điều kiện: `status=searchable`, `business_type` ∈ module catalog codes, **không** có bản ghi active tương ứng (`contract_records` / `dispatch_records` / `decision_records` / `procurement_records`).
- Response thêm `missing_module_metadata: boolean`; UI badge “Chưa có metadata module”.

### Kiến Trúc

```text
GET /documents/{id}/onboarding-suggestions
  -> DocumentRouter
  -> ModuleOnboardingService
       -> DocumentRepository (read document)
       -> Contract/Dispatch/Decision/ProcurementRepository (check active by document_id)
       -> mapping helper (document_type -> module, shared với worker audit)
```

Không thêm bảng DB Phase 14. Không đổi Qdrant/chunk.

### Smoke (Mục Tiêu 6)

`smoke_module_onboarding.py`: fixture text mỗi loại (`HĐ`, `CV` incoming/outgoing, `QĐ`, `KH`) → document searchable → GET onboarding-suggestions → assert `target_module` + key fields → PATCH business_type (optional) → POST module create với pre-fill.

## Hướng Dẫn Cho Mục Tiêu Tiếp Theo (Phase 14)

**Mục tiêu 2** thêm `ModuleOnboardingService`, schema `OnboardingSuggestionResponse`, router `GET .../onboarding-suggestions`.

**Mục tiêu 3** bổ sung audit `document.onboarding_suggested` trong worker (audit-only mặc định).

**Mục tiêu 4–5** frontend document detail banner + list filter `missing_module_metadata`.

**Mục tiêu 6** smoke `smoke_module_onboarding` + regression; đóng Phase 14.

---

## Document Relations — Liên Kết Chéo Văn Bản (Phase 15)

Trạng thái: triển khai (Phase 15 hoàn thành 2026-06-07).

### Vấn Đề

Hệ thống hiện có:

- **Nhiều tệp một document** (`document_files`) — cùng một văn bản nguồn, OCR gộp page/chunk.
- **Phụ lục trong cùng document** — chunk `section_role=appendix`, filter review queue/dashboard.

Chưa có:

- Liên kết **hai document độc lập** (upload riêng): công văn căn cứ quyết định, phụ lục hợp đồng scan riêng, công văn đính kèm hồ sơ mua sắm khác document gốc.

### Quyết Định MVP

| Hạng mục | Quyết định |
|----------|------------|
| Tên bảng | `document_relations` |
| Hướng quan hệ | Có hướng: `source_document_id` → `target_document_id` |
| Loại quan hệ | `references`, `appendix_of`, `implements`, `related` |
| Tạo quan hệ | Thủ công qua UI/API; không auto từ worker OCR Phase 15 |
| Xóa | Soft delete (`deleted_at`); không hard delete |
| Quyền | User đã login: tạo/xem; xóa: creator hoặc admin (ghi rõ khi implement mục tiêu 3) |

### `relation_type` (catalog cố định MVP)

| Code | Nhãn UI (gợi ý) | Ví dụ nghiệp vụ |
|------|------------------|-----------------|
| `references` | Tham chiếu / căn cứ | CV đề cập số QĐ … |
| `appendix_of` | Phụ lục của | PL hợp đồng scan riêng → HĐ gốc |
| `implements` | Triển khai / thực hiện | CV triển khai QĐ |
| `related` | Liên quan | Hồ sơ cùng gói, liên kết lỏng |

Hiển thị incoming đảo nhãn theo ngữ cảnh (ví dụ incoming `references` → “Được tham chiếu bởi”).

### Schema Đề Xuất

```text
document_relations
  id                  UUID PK
  source_document_id  FK documents.id NOT NULL
  target_document_id  FK documents.id NOT NULL
  relation_type       VARCHAR(32) NOT NULL
  notes               TEXT NULL
  created_by_user_id  FK users.id NULL
  created_at, updated_at, deleted_at
```

Ràng buộc:

- `source_document_id != target_document_id` (check service + DB constraint nếu khả thi).
- Partial unique index active: `(source_document_id, target_document_id, relation_type)` WHERE `deleted_at IS NULL`.
- Index: `(source_document_id)`, `(target_document_id)`, `(relation_type)`.

Không thêm cột `bidirectional` — nếu cần quan hệ hai chiều, user tạo hai bản ghi hoặc dùng `related` (MVP giữ đơn giản).

### API Shape

**GET** `/api/v1/documents/{document_id}/relations`

```json
{
  "document_id": "...",
  "outgoing": [
    {
      "id": "...",
      "relation_type": "references",
      "notes": null,
      "target_document": { "id", "title", "document_number", "document_type", "status" },
      "created_at": "..."
    }
  ],
  "incoming": [
    {
      "id": "...",
      "relation_type": "appendix_of",
      "source_document": { "id", "title", "document_number", "document_type", "status" },
      "created_at": "..."
    }
  ]
}
```

**POST** `/api/v1/documents/{document_id}/relations` (source = path `document_id`)

```json
{ "target_document_id": "...", "relation_type": "references", "notes": "optional" }
```

**DELETE** `/api/v1/document-relations/{relation_id}` — soft delete.

Audit metadata gọn: `source_document_id`, `target_document_id`, `relation_type`.

### Frontend UX (Mục Tiêu 4–5)

**Document detail** (`/documents/[id]`):

- Card **Văn bản liên quan** dưới banner onboarding / trên card module.
- Tab hoặc hai subsection: **Liên kết đi** (outgoing), **Liên kết đến** (incoming).
- Form thêm: autocomplete/chọn `document_id` đích (search list hiện có hoặc input UUID + validate), `relation_type`, `notes`.
- Mỗi dòng: nhãn quan hệ, link title → `/documents/{id}`, nút xóa (confirm).

**Document list** (mục tiêu 5 — tùy chọn):

- Response `relation_count` hoặc filter `has_relations=true` (document có ≥1 outgoing/incoming active).
- Badge nhỏ “N liên kết” trên `BaseDataTable` nếu `relation_count > 0`.

### Phân Biệt Với Chunk Appendix

| | `section_role=appendix` (chunk) | `document_relations` |
|--|--------------------------------|----------------------|
| Phạm vi | Trong một document | Giữa hai document |
| OCR | Tự động chunking | Không đổi pipeline |
| UI | Chunk filter review | Card liên kết document detail |

### Smoke (Mục Tiêu 6)

`smoke_document_relations.py`:

1. Seed document A (QĐ), B (CV).
2. POST B → A `references`.
3. GET relations B: outgoing 1; GET A: incoming 1.
4. POST trùng → 409.
5. DELETE → 404/empty.
6. Regression smokes Phase 14.

### Hướng Dẫn Cho Mục Tiêu Tiếp Theo (Phase 15)

**Mục tiêu 2** migration `0016_document_relations`, model SQLAlchemy.

**Mục tiêu 3** `DocumentRelationService`, router, audit, `smoke_document_relations`.

**Mục tiêu 4–5** frontend card + optional list badge/filter.

**Mục tiêu 6** regression + đóng phase.

---

## Relation Suggestions — Gợi Ý Liên Kết Từ Nội Dung (Phase 16)

Trạng thái: hoàn thành (2026-06-07). Smoke e2e `smoke_relation_suggestions` pass; regression Phase 15 pass.

### Vấn Đề

Phase 15 cho phép tạo `document_relations` **thủ công** — user phải biết document đích và nhập UUID hoặc tìm list. Trong thực tế, chunk OCR của công văn/quyết định/hợp đồng thường đã chứa số văn bản tham chiếu (“Căn cứ Quyết định số 02/QĐ-VT”, “Hợp đồng số 15/HĐ-…”, “kèm theo Phụ lục …”) nhưng hệ thống chưa **đối chiếu** các chuỗi đó với kho `documents` searchable.

### Quyết Định MVP

| Hạng mục | Quyết định |
|----------|------------|
| Cơ chế | Rule-based heuristic trên text chunk; **không** LLM, **không** embedding cross-document |
| Tạo liên kết | User xác nhận qua UI → `POST /documents/{id}/relations` hiện có; **không** auto-create |
| Service | `DocumentRelationSuggestionService.suggest_relations(document_id)` — read-only |
| API | `GET /api/v1/documents/{document_id}/relation-suggestions` |
| Giới hạn | Tối đa **8** gợi ý; dedupe `(target_document_id, relation_type)` |
| Phụ thuộc | Phase 15 (`document_relations`, `RELATION_TYPES`); classifier `document_number`; chunk `section_role` |

### Nguồn Dữ Liệu Chunk (Ưu Tiên Quét)

Đọc chunk qua `DocumentRepository.list_chunks_for_document`, lọc theo thứ tự ưu tiên:

1. **Trang 1–2** (`page_number` ∈ {1, 2} hoặc `chunk_index` thấp nhất khi thiếu `page_number`).
2. **`section_role`** ∈ `article`, `unknown` (bỏ `appendix`, `signature`, `recipient`, `task` trừ khi không còn chunk khác trên trang 1–2).
3. Chunk có anchor nhóm B (`ocr_chunking/anchors.py`: `Căn cứ`, `V/v`, `Thực hiện`, `Kèm theo` trong `GROUP_B_ANCHORS`) hoặc chứa pattern số/ký hiệu (xem Regex bên dưới).

Nếu sau lọc không còn chunk, fallback: toàn bộ chunk trang 1–2 bất kể `section_role`.

### Regex Trích Reference Candidate

Chuẩn hóa text chunk trước khi regex (mirror OCR classifier):

- NFC Unicode; gộp whitespace; trim dấu câu đầu/cuối (`DocumentClassifierService._clean_value`).
- Sửa OCR phổ biến trong symbol: `QD`→`QĐ`, `HD`→`HĐ`, `TB` giữ nguyên, `CV` giữ nguyên.

**Pattern chính** — bắt `number/symbol` hành chính VN (ưu tiên có tiền tố loại văn bản hoặc “số”):

```text
(?:Căn\s*cứ\s+)?(?:Quyết\s*định|Q[ĐD]|Công\s*văn|CV|Hợp\s*đồng|H[ĐD]|Thông\s*báo|TB|Chỉ\s*thị|CT|Nghị\s*quyết|NQ)\s*
(?:số\s*)?(?P<num>\d+)\s*/\s*(?P<sym>[A-ZÀ-ỸĐa-zà-ỹ][A-ZÀ-ỸĐa-zà-ỹ0-9.\-]*)
```

**Pattern phụ** — “Số: …” inline (cùng logic classifier `_extract_document_number_and_symbol`):

```text
\bSố\s*:\s*(?P<full>[^\n]{3,80})
```

Tách `full` tại `/` đầu tiên → `num` + `sym`; cắt phần sau nếu gặp `ngày` hoặc khoảng trắng kép (giống classifier dòng 189).

**Pattern phụ** — số/ký hiệu đứng độc lập (confidence thấp hơn):

```text
\b(?P<num>\d{1,4})\s*/\s*(?P<sym>Q[ĐD][-\w]*|CV[-\w]*|H[ĐD][-\w]*|TB[-\w]*|NQ[-\w]*|CT[-\w]*|[A-ZĐ]{2,}[-\w]*)
```

Mỗi match sinh `matched_reference` = chuỗi gốc (trim, ≤128 ký tự) và `normalized_number` = `{num}/{sym}` sau normalize.

### Normalize `document_number` (Lookup)

Hàm `normalize_document_number(value: str) -> str | None` — **tái dùng logic classifier** (mục tiêu 2 có thể extract shared helper từ `DocumentClassifierService`):

1. `_clean_value` (whitespace, trim `.;,:`).
2. Cắt phần date/place nếu dính sau số (regex `(?=\b[A-ZÀ-Ỹ][a-zà-ỹ]+,\s*ngày\b)` hoặc `\s{2,}`).
3. Symbol OCR fix: `QD`→`QĐ`, `HD`→`HĐ` (chỉ phần sau `/`).
4. So khớp DB: **case-insensitive exact** trên `documents.document_number` (`ILIKE` hoặc `LOWER()`); chỉ document `status = 'searchable'`, `deleted_at IS NULL`.

**Chiến lược match document đích** (theo thứ tự):

| Bước | Điều kiện | Ghi chú |
|------|-----------|---------|
| 1 | `normalized_number` khớp exact `document_number` | Bắt buộc MVP |
| 2 | Nhiều kết quả | Ưu tiên `document_type` suy từ prefix symbol (`QĐ`, `CV`, `HĐ`); nếu vẫn hòa → bỏ qua (không đoán) |
| 3 | Không khớp | Không gợi ý; **không** fuzzy/embedding |

Fallback tùy chọn (chỉ khi bước 1 thất bại và symbol đủ dài): `document_symbol` + `num` — **ngoài MVP mục tiêu 2** nếu chưa có index; ghi nhận để mở rộng sau.

### Anchor Phrase → `relation_type`

Quét **cùng chunk** hoặc **chunk liền trước** (cùng document, `chunk_index - 1`) trong cửa sổ 200 ký tự trước `matched_reference`. Áp dụng rule **ưu tiên cao → thấp** (rule đầu khớp thắng):

| Anchor / ngữ cảnh (regex, `IGNORECASE`) | `relation_type` | Ghi chú |
|----------------------------------------|-----------------|---------|
| `\bCăn\s*cứ\b`, `\bcăn\s*cứ\b`, `\bXét\b` | `references` | CV/QĐ tham chiếu văn bản nền |
| `\bPhụ\s*lục\b`, `\bKèm\s*theo\b`, `\bđính\s*kèm\b` + symbol `HĐ`/`HD` trong reference | `appendix_of` | Phụ lục hợp đồng scan riêng |
| `\bThực\s*hiện\b`, `\btriển\s*khai\b`, `\bTổ\s*chức\s*thực\s*hiện\b` | `implements` | CV triển khai QĐ/KH |
| Khớp số nhưng không có anchor rõ | `related` | Liên kết lỏng, cần review |

`relation_type` phải ∈ `RELATION_TYPES` Phase 15 (`references`, `appendix_of`, `implements`, `related`).

### Loại Trừ (Bắt Buộc)

Service **không** đưa vào danh sách gợi ý khi:

| Loại trừ | Kiểm tra |
|----------|----------|
| **Self-link** | `target_document_id == source_document_id` |
| **Relation active trùng triple** | Đã tồn tại `(source_document_id, target_document_id, relation_type)` với `deleted_at IS NULL` |
| **Target không searchable** | `documents.status != 'searchable'` hoặc `deleted_at IS NOT NULL` |
| **Source không searchable** | API layer trả `404` hoặc `[]` — service không chạy heuristic |

Document nguồn không tồn tại / đã xóa: API `404` (mục tiêu 3).

### Confidence Và Ngưỡng UI

Điểm `confidence` ∈ [0.0, 1.0]; `reasons[]` giải thích từng thành phần (debug + UI tooltip).

**Công thức gợi ý** (cộng dồn, cap 1.0):

| Thành phần | Điểm | `reasons[]` mẫu |
|------------|------|-----------------|
| Exact match `document_number` | +0.55 | `exact_document_number_match` |
| Pattern chính (có tiền tố loại VB) | +0.20 | `strong_reference_pattern` |
| Pattern phụ / standalone | +0.10 | `weak_reference_pattern` |
| Anchor phrase khớp `relation_type` | +0.15 | `anchor:can_cu` / `anchor:phu_luc` / … |
| Chunk trang 1 | +0.05 | `source_page_1` |
| Chunk `section_role=article` | +0.05 | `source_section_article` |

**Ngưỡng hiển thị** (field `confidence_tier` trong response — không lưu DB):

| Tier | Điều kiện | UX |
|------|-----------|-----|
| `high` | `confidence >= 0.80` | Nút **Tạo liên kết** nổi bật |
| `review` | `0.50 <= confidence < 0.80` | Style nhắc xem lại; vẫn cho phép tạo |
| (ẩn) | `< 0.50` | Không trả về client |

Không chặn workflow: tier `review` vẫn hiển thị; user quyết định.

### DTO Gợi Ý

**`RelationSuggestionRead`** (Pydantic, mục tiêu 3):

```json
{
  "target_document_id": "uuid",
  "relation_type": "references",
  "confidence": 0.92,
  "confidence_tier": "high",
  "matched_reference": "Quyết định số 01/QD-REL-abc",
  "source_chunk_id": "uuid",
  "source_chunk_quote": "Căn cứ Quyết định số 01/QD-REL-abc của Giám đốc...",
  "target_document_preview": {
    "id": "uuid",
    "title": "...",
    "document_number": "01/QD-REL-abc",
    "document_type": "QĐ",
    "status": "searchable"
  },
  "reasons": ["exact_document_number_match", "strong_reference_pattern", "anchor:can_cu", "source_page_1"]
}
```

| Field | Bắt buộc | Mô tả |
|-------|----------|-------|
| `target_document_id` | ✓ | UUID document đích đã match |
| `relation_type` | ✓ | Một trong `RELATION_TYPES` |
| `confidence` | ✓ | Float 0–1 |
| `confidence_tier` | ✓ | `high` \| `review` |
| `matched_reference` | ✓ | Chuỗi regex bắt được |
| `source_chunk_id` | ✓ | Chunk nguồn |
| `source_chunk_quote` | ✓ | Trích ≤200 ký tự quanh reference (UI quote) |
| `target_document_preview` | ✓ | Snapshot gọn cho UI (không embed full relations) |
| `reasons` | ✓ | Mảng string, thứ tự ổn định |

**`RelationSuggestionsResponse`**:

```json
{
  "document_id": "uuid",
  "suggestions": [ "...RelationSuggestionRead..." ],
  "candidate_count": 1
}
```

Dedupe: giữ bản ghi **confidence cao nhất** cho mỗi `(target_document_id, relation_type)`.

### API Shape (Mục Tiêu 3)

**GET** `/api/v1/documents/{document_id}/relation-suggestions`

- Auth: user đăng nhập (giống GET relations).
- `404`: document không tồn tại / đã xóa.
- `404` hoặc `[]`: document không `searchable` (implement chọn một — khuyến nghị `404` với message rõ cho document chưa OCR xong).
- Không side-effect; không ghi `document_relations`.
- Audit tùy chọn: `document.relation_suggested`, metadata `{ "candidate_count": N }` — chỉ nếu không làm chậm smoke.

### Frontend UX (Mục Tiêu 4–5 — Tham Chiếu)

Subsection **Gợi ý liên kết** trong `DocumentRelationsCard`:

- `high`: border/emphasis mặc định; `review`: badge “Cần xem lại”.
- Hiển thị: nhãn `relation_type`, `target_document_preview.document_number`, `source_chunk_quote`.
- **Tạo liên kết** → `POST /documents/{source_id}/relations` (≤2 thao tác).
- **Bỏ qua** → client-side dismiss (session/ref Set); không API.

### Smoke Fixture (Mục Tiêu 6)

Mirror `smoke_document_relations`:

1. Seed QĐ A: `document_number = 01/QD-REL-{suffix}`, `status = searchable`, chunk text trang 1 (metadata classifier).
2. Seed CV B: searchable, chunk chứa `Căn cứ Quyết định số 01/QD-REL-{suffix}`.
3. `GET .../relation-suggestions` trên B → ≥1 gợi ý, `target_document_id = A`, `relation_type = references`, `confidence_tier` ∈ {`high`, `review`}.
4. `POST` relation B→A → gợi ý biến mất (triple đã tồn tại).

### Phân Biệt Với Phase 15 / Chunk Appendix

| | Chunk `section_role=appendix` | Relation suggestion |
|--|------------------------------|---------------------|
| Phạm vi | Trong một document | Giữa hai document searchable |
| Tự động | Chunking pipeline | Heuristic read-only; user xác nhận |
| Lưu trữ | `document_chunks` | Chỉ gợi ý; persist qua `document_relations` khi user POST |

### Triển Khai Hoàn Tất (Phase 16)

- Backend: `DocumentRelationSuggestionService`, `GET /api/v1/documents/{document_id}/relation-suggestions`, shared `normalize_document_number`.
- Frontend: subsection **Gợi ý liên kết** trong `DocumentRelationsCard`, apply/dismiss UX, refresh relations sau POST.
- Smoke: `smoke_relation_suggestions` (e2e CV→QĐ), `smoke_document_relation_suggestions_repo` (repo-level).

---

## RAG Generative — Local LLM (Phase 17)

Trạng thái: thiết kế (mục tiêu 1 hoàn thành 2026-06-07). Triển khai code từ mục tiêu 2.

### Vấn Đề

Phase 3/9/12 đã có RAG **extractive**: `RagAnswerService._compose_answer()` nối quote từ top 1–2 citation — đủ MVP, không tổng hợp đa chunk bằng ngôn ngữ tự nhiên. User hỏi câu phức tạp (so sánh điều khoản, tóm tắt nghĩa vụ) cần câu trả lời **generative** nhưng vẫn phải truy vết nguồn chunk (citation bắt buộc, on-prem, không cloud).

### Quyết Định MVP

| Hạng mục | Quyết định |
|----------|------------|
| LLM runtime | **Ollama** — HTTP `/api/chat` (OpenAI-compatible messages) |
| Generation backend | `RAG_GENERATION_BACKEND=extractive \| ollama` — **mặc định `extractive`** |
| Retrieval | Giữ nguyên `SearchService.semantic_search` + filter metadata module — **không** re-index Qdrant |
| Endpoint | Một endpoint `POST /api/v1/search/answer` — thêm field response, không tách route mới |
| Citation | Bắt buộc; post-validate trước khi trả `grounded=true` + `generation_mode=generative` |
| Fallback | LLM down/timeout/validation fail → **extractive path hiện tại** (identical Phase 12) |
| Readiness | `/health/ready` **không** kiểm tra Ollama — API vẫn ready khi LLM degraded |
| Worker OCR | **Không** gọi LLM — generation sync trên request RAG only |
| vLLM / cloud | **Không** trong MVP |

### Luồng Xử Lý

```text
POST /search/answer (RagAnswerRequest — giữ nguyên)
  -> SearchService.semantic_search(query, filters, limit)
  -> evidence = filter min_score + query overlap (logic hiện tại)
  -> nếu evidence rỗng hoặc insufficient_evidence:
       return extractive fallback (fallback_reason=insufficient_evidence)
  -> nếu RAG_GENERATION_BACKEND != ollama:
       return extractive path (_compose_answer) — generation_mode=extractive
  -> LocalLLMService.is_available() == false:
       return extractive path — generation_mode=extractive, fallback_reason=llm_unavailable
  -> RagContextBuilder.build(evidence) -> numbered context blocks [1]..[n]
  -> LocalLLMService.generate(system, user) — timeout RAG_LLM_TIMEOUT_SECONDS
  -> CitationValidator.validate(raw_answer, evidence, markers [n])
  -> nếu validation fail:
       return extractive path — fallback_reason=validation_failed
  -> map markers -> RagCitation[] (chunk_id, quote từ evidence, metadata giữ nguyên)
  -> return { answer, grounded=true, generation_mode=generative, citations, model_name, latency_ms }
```

**Nguyên tắc:** nhánh extractive fallback phải tái sử dụng code `_compose_answer` / `_citation` hiện có — không duplicate logic evidence.

### Schema Response (Mở Rộng)

Giữ backward compatible — field mới **optional** (Pydantic + frontend TypeScript):

| Field | Type | Mặc định | Ghi chú |
|-------|------|----------|---------|
| `generation_mode` | `extractive \| generative` | `extractive` | Client hiển thị badge dashboard |
| `model_name` | `str \| null` | `null` | Chỉ khi generative thành công |
| `latency_ms` | `int \| null` | `null` | Thời gian gọi Ollama |
| `fallback_reason` | mở rộng | — | Thêm `llm_unavailable`, `validation_failed`; giữ `insufficient_evidence` |

`RagCitation` **không đổi** — deep-link `#chunk-{id}` Phase 12 vẫn dùng được.

### RagContextBuilder (Mục Tiêu 4)

Format mỗi block context (tiếng Việt, numbered `[1]`..`[n]`):

```text
[1] chunk_id=<uuid> | <title> | Số: <document_number> | Trang <page_from>-<page_to> | <section_path joined>
<text snippet — cắt tối đa ~600 ký tự/chunk, ưu tiên câu có overlap query>
```

- `n` = `min(len(evidence), max_citations)` — tối đa 8 theo request.
- Tổng context ≤ `RAG_LLM_MAX_CONTEXT_CHARS` — cắt từ chunk score thấp nếu vượt.
- Không đưa chunk `requires_review=true` vào context **trừ khi** không còn evidence khác (giữ parity search filter hiện tại).

### Prompt MVP

**System message (tiếng Việt):**

```text
Bạn là trợ lý tra cứu văn bản hành chính tiếng Việt. Chỉ trả lời dựa trên các đoạn [1]..[n] được cung cấp.
- Không bịa số văn bản, điều khoản hoặc nội dung không có trong context.
- Mỗi ý quan trọng phải kèm tham chiếu [số] tương ứng đoạn nguồn.
- Nếu context không đủ trả lời, trả lời ngắn: "Không đủ căn cứ trong các đoạn đã cung cấp." và không thêm thông tin ngoài context.
- Trả lời súc tích, tiếng Việt chuẩn hành chính.
```

**User message:**

```text
Câu hỏi: {query}

Các đoạn tham chiếu:
{numbered_context_blocks}

Trả lời câu hỏi và trích [n] cho mỗi ý dựa trên đoạn tương ứng.
```

**Generation params:** `temperature=RAG_LLM_TEMPERATURE` (mặc định 0.1), `num_predict=RAG_LLM_MAX_OUTPUT_TOKENS`.

### CitationValidator

Validation **bắt buộc** trước khi chấp nhận generative:

1. **Marker parse:** regex `\[\d+\]` trong `raw_answer`; mỗi index `n` phải ∈ `1..len(evidence)`.
2. **Non-empty markers:** nếu `grounded` generative yêu cầu ≥1 marker hợp lệ (trừ câu “Không đủ căn cứ…” → `grounded=false`, fallback extractive hoặc insufficient).
3. **Quote mapping:** `citations[i].quote` lấy từ evidence chunk tương ứng (không tin quote LLM tự viết) — giống extractive `_quote()`.
4. **chunk_id whitelist:** mọi `chunk_id` trong response phải thuộc retrieval set của request.
5. **Fail validation** → fallback extractive, `fallback_reason=validation_failed`, log warning (không 500).

### Fallback Reason Contract

| `fallback_reason` | Điều kiện | `generation_mode` | `grounded` |
|-------------------|-----------|-------------------|------------|
| `null` | Extractive hoặc generative thành công | tương ứng | true/false theo logic hiện tại |
| `insufficient_evidence` | Không đủ overlap/score (logic hiện tại) | `extractive` | false |
| `llm_unavailable` | Ollama unreachable, timeout, model chưa load | `extractive` | theo extractive |
| `validation_failed` | LLM trả lời nhưng fail CitationValidator | `extractive` | theo extractive |

Frontend (`RagAnswerPanel`): hiển thị hint riêng cho `llm_unavailable` / `validation_failed` (mục tiêu 6).

### Hợp Đồng Env

| Biến | Mặc định dev | Ghi chú |
|------|--------------|---------|
| `RAG_GENERATION_BACKEND` | `extractive` | `ollama` khi bật profile `llm` |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Remote host prod: `http://llm-host:11434` |
| `RAG_LLM_MODEL` | `qwen2.5:3b-instruct` | Prod khuyến nghị `qwen2.5:7b-instruct` |
| `RAG_LLM_TIMEOUT_SECONDS` | `120` | Dev CPU; prod GPU ~90 |
| `RAG_LLM_MAX_CONTEXT_CHARS` | `8000` | Prod có thể 12000 |
| `RAG_LLM_MAX_OUTPUT_TOKENS` | `512` | Prod có thể 768 |
| `RAG_LLM_TEMPERATURE` | `0.1` | Thấp để giảm hallucination |
| `OLLAMA_CPU_LIMIT` | `2` | Compose limit |
| `OLLAMA_MEMORY_LIMIT` | `6G` | Dev 3B; prod CPU 10G |

Settings Pydantic (mục tiêu 2): mirror naming `embedding_backend` → `rag_generation_backend`, snake_case, đọc từ `.env`.

### LocalLLMService (Mục Tiêu 2 — Interface)

```python
class LocalLLMService:
    def is_available(self) -> bool: ...  # GET {OLLAMA_BASE_URL}/api/tags hoặc /api/version, timeout ngắn
    def generate(self, *, system: str, user: str) -> GenerateResult: ...  # text, model, latency_ms
```

- HTTP client `urllib` hoặc `httpx` nếu đã có dependency — **không** thêm SDK cloud.
- Timeout cứng = `RAG_LLM_TIMEOUT_SECONDS`.
- Exception → caller (`RagAnswerService`) catch → fallback, không propagate 500.

### Ops / Health (Mục Tiêu 5)

- `/health/ready`: postgres, redis, qdrant, uploads — **không** ollama.
- `/ops/system-status`: component `llm` — `ok` / `degraded` / `unavailable`; metadata `backend`, `model`, `reachable`, `generation_backend` setting.

### Phân Biệt Extractive vs Generative

| | Extractive (Phase 12) | Generative (Phase 17) |
|--|----------------------|------------------------|
| Answer | `"Dựa trên các đoạn đã truy xuất: " + quote nối` | LLM tổng hợp + markers `[n]` |
| Phụ thuộc Ollama | Không | Có (optional) |
| Smoke mặc định | `smoke_rag_answer` | `smoke_rag_generative` (profile `llm`) |
| CI default | Pass không Ollama | Generative smoke optional / nightly |

### Triển Khai Hoàn Tất (Phase 17)

Tất cả mục tiêu Phase 17 đã triển khai (2026-06-07):

- `LocalLLMService` + settings; Docker Compose service `ollama`, profile `llm`, volume `ollama_data`.
- `RagContextBuilder`, `CitationValidator`, nhánh generative + fallback trong `RagAnswerService`.
- Schema/API `generation_mode`, ops LLM status; frontend dashboard + `/status`.
- Runbook `docs/RAG_LLM_RUNBOOK.md`; smoke `smoke_rag_generative` (profile `llm`).

Smoke mặc định CI/dev: `smoke_rag_answer` (extractive, không Ollama). Smoke generative: `docs/RAG_LLM_RUNBOOK.md`.

---

## Procurement Line Items (Phase 18)

Trạng thái: thiết kế đã chốt (2026-06-08, mục tiêu 1). Triển khai code từ mục tiêu 2.

### Vấn Đề

Phase 13 (`procurement_records`) chỉ lưu metadata cấp hồ sơ — `reference_number`, `estimated_value`, `requesting_unit`, … — **không** có bảng con cho từng mặt hàng. OCR/chunk thường chứa bảng vật tư (STT, tên, đơn vị, số lượng, đơn giá, thành tiền) nhưng chưa được cấu trúc hóa. Phòng vật tư cần tra cứu "hồ sơ nào có mặt hàng X" và tổng giá trị theo dòng — **chưa** cần quản lý tồn kho thực tế.

### Phụ Thuộc Phase 13 (Không Đổi Document/Chunk Core)

| Thành phần | Quyết định |
|------------|------------|
| `procurement_records` | Giữ nguyên schema Phase 13; line items FK `procurement_id` |
| Liên kết document | Vẫn qua `procurement_records.document_id` — **không** thêm `document_id` trên line item |
| `documents` / `document_chunks` | **Không** sửa schema, worker OCR, chunking, Qdrant payload |
| Search/RAG retrieval | Vẫn vector trên chunk; filter mặt hàng **pre-resolve** `document_id` qua PostgreSQL (pattern Phase 11) |
| Onboarding Phase 14 | Không đổi; gợi ý procurement metadata vẫn ở cấp hồ sơ |
| RBAC module | Mirror procurement hiện có |

### Quyết Định Kiến Trúc MVP

| Hạng mục | Quyết định | Lý do |
|----------|------------|-------|
| Bảng dòng hàng | `procurement_line_items` — FK `procurement_id`, soft delete | 1 procurement có N dòng; tách khỏi document core |
| Danh mục vật tư | `materials_catalog` — bảng riêng (không dùng `admin_catalog_items`) | Metadata vật tư (`default_unit`, `category`) khác catalog upload |
| Liên kết catalog | `catalog_item_id` optional FK → `materials_catalog`; snapshot `item_name`/`item_code`/`unit` trên dòng | Autocomplete + lưu giá trị đã nhập khi catalog bị ẩn/xóa mềm |
| Tồn kho | **Không** `stock_quantity`, phiếu xuất/nhập | Phase 19+ |
| Workflow phê duyệt | **Không** rule engine, assignee, SLA | User PATCH `status` procurement như Phase 13 |
| Pre-fill OCR | Tùy chọn mục tiêu 6 — read-only suggestion, user xác nhận | Không auto-insert |
| Search | `procurement_item_name` / `procurement_item_code` pre-resolve `document_id` | Mirror Phase 11; không re-index Qdrant |

Luồng nghiệp vụ:

```text
document searchable + procurement_record (Phase 13)
  -> user thêm/sửa/xóa line items (form UI hoặc áp dụng gợi ý OCR)
  -> service tính amount từng dòng; UI hiển thị tổng sum(amount)
  -> cảnh báo nhẹ khi sum(amount) lệch estimated_value (không chặn lưu)
  -> list/filter procurement theo item_name / item_code
  -> search/RAG dashboard filter procurement_item_name / procurement_item_code
```

### Tên Kỹ Thuật

| Thực thể | Giá trị |
|----------|---------|
| Bảng dòng hàng | `procurement_line_items` |
| Model | `ProcurementLineItem` |
| Bảng catalog | `materials_catalog` |
| Model catalog | `MaterialsCatalogItem` |
| Entity audit line item | `procurement_line_item` |
| Entity audit catalog | `materials_catalog` |
| API line items nested | `/api/v1/procurements/{procurement_id}/line-items` |
| API line items flat | `/api/v1/procurement-line-items/{line_item_id}` |
| API catalog | `/api/v1/materials-catalog` |

### Schema `procurement_line_items`

Migration đề xuất: `0017_procurement_line_items` (mục tiêu 2).

| Cột | Kiểu | Bắt buộc | Mô tả |
|-----|------|----------|-------|
| `id` | UUID | ✓ | Primary key |
| `procurement_id` | UUID FK → `procurement_records.id` | ✓ | Hồ sơ mua sắm cha |
| `line_number` | `Integer` | ✓ | Thứ tự hiển thị (1-based); unique active theo procurement |
| `item_name` | `String(512)` | ✓ | Tên vật tư/hàng hóa |
| `item_code` | `String(64)` | — | Mã vật tư (optional; có thể copy từ catalog) |
| `unit` | `String(32)` | — | Đơn vị tính (cái, bộ, kg, …) |
| `quantity` | `Numeric(18, 4)` | ✓ | Mặc định `1`; validate `>= 0` |
| `unit_price` | `Numeric(18, 2)` | — | Đơn giá; validate `>= 0` nếu có |
| `amount` | `Numeric(18, 2)` | — | Thành tiền — **tính server-side** (xem mục Amount) |
| `catalog_item_id` | UUID FK → `materials_catalog.id` | — | Tham chiếu catalog khi chọn autocomplete; `ON DELETE SET NULL` |
| `notes` | `Text` | — | Ghi chú dòng |
| `created_at`, `updated_at`, `deleted_at` | timestamptz | ✓ | Audit + soft delete |

**Indexes:**

- `ux_procurement_line_items_procurement_line_active`: unique partial `(procurement_id, line_number)` WHERE `deleted_at IS NULL`.
- `ix_procurement_line_items_procurement_active`: `(procurement_id, deleted_at)` — list theo hồ sơ.
- `ix_procurement_line_items_item_name_active`: `(item_name, deleted_at)` — filter `ILIKE` list/search.
- `ix_procurement_line_items_item_code_active`: `(item_code, deleted_at)` — filter mã vật tư.

**Quan hệ model:**

- `ProcurementRecord.line_items` — `uselist=True`, order_by `line_number`.
- `ProcurementLineItem.procurement` — back_populates.
- `ProcurementLineItem.catalog_item` — optional, `uselist=False`.

Không copy OCR text/chunk vào bảng line item. Không denormalize `document_id`.

### Cách Tính `amount` (Server-Side)

Service (`ProcurementLineItemService`) **luôn** chuẩn hóa trước persist và trả response:

| Input | Quy tắc |
|-------|---------|
| `quantity` + `unit_price` đều có | `amount = round(quantity * unit_price, 2)` — **server ghi đè** nếu client gửi `amount` khác |
| Chỉ `unit_price`, thiếu `quantity` | `quantity = 1` rồi tính như trên |
| Chỉ `quantity`, không `unit_price` | `amount = null` (trừ khi client gửi `amount` explicit — xem dòng dưới) |
| Client gửi `amount` explicit, không có `unit_price` | Lưu `amount` đã gửi (validate `>= 0`); dùng cho dòng "thành tiền cố định" không tách đơn giá |
| Không `unit_price`, không `amount` | `amount = null` |

**Response read:** luôn trả `amount` đã persist (sau tính toán). UI tổng cộng: `lines_total_amount = sum(amount)` chỉ cộng dòng có `amount IS NOT NULL`.

**Đối chiếu `estimated_value`:** chỉ cảnh báo UI (Message warn) khi `|lines_total_amount - estimated_value| / estimated_value > 0.01` (1%) và cả hai phía có giá trị — **không** validation API 422, không rule engine.

### Schema `materials_catalog`

Migration đề xuất: `0018_materials_catalog` (mục tiêu 4; có thể gộp `0017` nếu migration nhỏ).

| Cột | Kiểu | Bắt buộc | Mô tả |
|-----|------|----------|-------|
| `id` | UUID | ✓ | Primary key |
| `code` | `String(64)` | — | Mã vật tư chuẩn nội bộ (optional) |
| `name` | `String(255)` | ✓ | Tên vật tư — dùng autocomplete |
| `default_unit` | `String(32)` | — | ĐVT mặc định khi chọn catalog |
| `category` | `String(128)` | — | Nhóm (văn phòng phẩm, IT, …) — optional |
| `description` | `Text` | — | Mô tả ngắn |
| `is_active` | `Boolean` | ✓ | Default `true`; false = ẩn khỏi autocomplete user |
| `created_at`, `updated_at`, `deleted_at` | timestamptz | ✓ | Audit + soft delete |

**Unique constraint (chốt MVP):**

| Index | Phạm vi | Quy tắc |
|-------|---------|---------|
| `ux_materials_catalog_code_active` | Partial `deleted_at IS NULL` AND `code IS NOT NULL` AND `trim(code) <> ''` | Unique trên `lower(trim(code))` — mã vật tư không trùng (case-insensitive) |
| `ux_materials_catalog_name_active` | Partial `deleted_at IS NULL` | Unique trên `lower(trim(name))` — tên không trùng trong catalog active |

- Cho phép nhiều bản ghi **không có** `code` (chỉ unique khi `code` non-empty).
- Admin tạo trùng tên/code → `409 Conflict`.
- Soft delete catalog **không** xóa/sửa line item đã lưu: dòng giữ snapshot `item_name`/`item_code`/`unit`; `catalog_item_id` có thể trỏ bản ghi đã `deleted_at IS NOT NULL` (read-only lịch sử) hoặc SET NULL khi hard policy — MVP giữ FK, ẩn khỏi autocomplete (`is_active=false` hoặc soft delete).

**Indexes bổ sung:**

- `ix_materials_catalog_name_active`: `(name, deleted_at)` — autocomplete `ILIKE`.
- `ix_materials_catalog_is_active`: `(is_active, deleted_at)`.

**Seed dev (mục tiêu 4):** vài mã mẫu trong migration seed hoặc smoke script — ví dụ `VT-001` / `Giấy A4`, `VT-002` / `Mực in HP`, `default_unit` = `Ram` / `Hộp`.

### API Contract — Line Items

Router nested gắn `procurements` router; flat router riêng (đặt **sau** nested routes để tránh nuốt path).

| Method | Path | Mô tả |
|--------|------|--------|
| `GET` | `/api/v1/procurements/{procurement_id}/line-items` | List dòng active, sort `line_number ASC` |
| `POST` | `/api/v1/procurements/{procurement_id}/line-items` | Tạo dòng; auto `line_number` = max+1 nếu client không gửi |
| `PATCH` | `/api/v1/procurement-line-items/{line_item_id}` | Cập nhật; recalc `amount` |
| `DELETE` | `/api/v1/procurement-line-items/{line_item_id}` | Soft delete (**admin**) |

**Request body — create (`ProcurementLineItemCreateRequest`):**

```json
{
  "line_number": 1,
  "item_name": "Giấy A4",
  "item_code": "VT-001",
  "unit": "Ram",
  "quantity": "10",
  "unit_price": "85000.00",
  "catalog_item_id": "uuid-or-null",
  "notes": null
}
```

**Request body — update (`ProcurementLineItemUpdateRequest`):** mọi field optional; omit = không đổi.

**Response item (`ProcurementLineItemRead`):**

```json
{
  "id": "uuid",
  "procurement_id": "uuid",
  "line_number": 1,
  "item_name": "Giấy A4",
  "item_code": "VT-001",
  "unit": "Ram",
  "quantity": "10.0000",
  "unit_price": "85000.00",
  "amount": "850000.00",
  "catalog_item_id": "uuid-or-null",
  "notes": null,
  "created_at": "...",
  "updated_at": "..."
}
```

**List response (`ProcurementLineItemListResponse`):**

```json
{
  "items": ["...ProcurementLineItemRead..."],
  "total": 3,
  "lines_total_amount": "1250000.00"
}
```

Không pagination line items MVP (typical ≤50 dòng/hồ sơ). `404` nếu `procurement_id` không tồn tại / đã xóa mềm.

### API Contract — Materials Catalog

| Method | Path | Quyền | Mô tả |
|--------|------|-------|--------|
| `GET` | `/api/v1/materials-catalog` | User đăng nhập | List **active** (`deleted_at IS NULL` AND `is_active=true`); query `q`, `limit` (default 20, max 50) — autocomplete |
| `GET` | `/api/v1/materials-catalog/{catalog_id}` | User | Chi tiết (kể cả inactive — read-only cho admin UI) |
| `GET` | `/api/v1/materials-catalog/all` | Admin | List đầy đủ + filter `q`, `is_active`, `category`, pagination |
| `POST` | `/api/v1/materials-catalog` | Admin | Tạo |
| `PATCH` | `/api/v1/materials-catalog/{catalog_id}` | Admin | Cập nhật |
| `DELETE` | `/api/v1/materials-catalog/{catalog_id}` | Admin | Soft delete |

Route `/all` đặt trước `/{catalog_id}` trên router. Autocomplete user chỉ trả `id`, `code`, `name`, `default_unit`, `category`.

Lỗi: `404` not found; `409` trùng `code`/`name` active; `403` user gọi mutating admin routes.

### Quyền Và Audit

**Line items** — mirror procurement (Phase 13):

| Hành động | User đăng nhập | Admin |
|-----------|----------------|-------|
| List / get theo procurement | Có | Có |
| Create / update | Có | Có |
| Soft delete | Không (`403`) | Có |

**Materials catalog:**

| Hành động | User | Admin |
|-----------|------|-------|
| List active (autocomplete) / get | Có | Có |
| CRUD / soft delete / list all | Không (`403`) | Có |

**Audit actions:**

| Action | `entity_type` | Metadata JSON gọn |
|--------|---------------|-------------------|
| `procurement_line_item.created` | `procurement_line_item` | `procurement_id`, `line_number`, `item_name` |
| `procurement_line_item.updated` | `procurement_line_item` | `procurement_id`, changed fields |
| `procurement_line_item.deleted` | `procurement_line_item` | `procurement_id`, `line_number` |
| `materials_catalog.created` | `materials_catalog` | `code`, `name` |
| `materials_catalog.updated` | `materials_catalog` | changed fields |
| `materials_catalog.deleted` | `materials_catalog` | `code`, `name` |

### Filter List Procurement Theo Mặt Hàng (Mục Tiêu 7)

Mở rộng `GET /api/v1/procurements`:

| Query param | Match logic |
|-------------|-------------|
| `item_name` | `EXISTS` join `procurement_line_items` active: `item_name ILIKE %value%` |
| `item_code` | `EXISTS` join active: `item_code ILIKE %value%` |

Kết hợp với filter Phase 13 (`procurement_kind`, `reference_number`, …) bằng AND.

Repository: `ProcurementRepository.list_procurements` / `count_procurements` / `list_document_ids_by_metadata` nhận thêm `item_name`, `item_code`.

### Filter Search / RAG (Mục Tiêu 7)

Mở rộng `POST /api/v1/search/semantic` và `POST /api/v1/search/answer` — schema `SemanticSearchRequest` / `RagAnswerRequest`:

| Tham số API | Repository param | Match logic |
|-------------|------------------|-------------|
| `procurement_item_name` | `item_name` | `procurement_line_items.item_name ILIKE %value%` join `procurement_records` → `document_id` |
| `procurement_item_code` | `item_code` | `procurement_line_items.item_code ILIKE %value%` |

**Kích hoạt nhóm filter procurement:** `_resolve_procurement_document_ids` active khi có **bất kỳ** tham số: `procurement_kind`, `procurement_status`, `reference_number`, `requesting_unit`, **`procurement_item_name`**, **`procurement_item_code`**.

Implementation (mục tiêu 7):

```text
ProcurementLineItemRepository.list_document_ids_by_item_metadata(
  item_name?, item_code?
) -> list[str] document_id

ProcurementRepository.list_document_ids_by_metadata(..., item_name?, item_code?)
  -> join hoặc subquery EXISTS line items (chỉ deleted_at IS NULL)
```

Intersection với contract/dispatch/decision groups giữ nguyên Phase 11. **Không** sửa Qdrant payload, **không** re-index chunk.

Enrich `SemanticSearchResult`: không bắt buộc thêm field line item MVP — optional `matched_item_name` sau nếu cần UX; mục tiêu 7 tối thiểu filter đúng `document_id`.

Dashboard preset từ `/procurements`: thêm query `procurement_item_name`, `procurement_item_code` khi có filter mặt hàng trên UI list.

### Boundary Kỹ Thuật

**Backend:**

```text
router -> service -> repository
```

- `ProcurementLineItemService` validate procurement tồn tại (active) trước create.
- `MaterialsCatalogService` tách riêng; không gom vào `CatalogService` admin upload.
- Router không chứa business logic tính `amount`.

**Frontend (mục tiêu 5 — tham chiếu):**

```text
page -> composable -> service -> API
```

- `useProcurementLineItems`, `useMaterialsCatalog`; types `procurement-line-item.ts`, `materials-catalog.ts`.
- UI dòng hàng trên trang/modal `/procurements`; admin section `/materials-catalog`.
- Không gọi API trực tiếp trong component.

### Không Làm Trong Phase 18

- Không `stock_quantity`, phiếu xuất/nhập, tồn tối thiểu, kho vật lý.
- Không workflow trình ký/phê duyệt nhiều bước, assignee, SLA, comment thread.
- Không LLM trích xuất bảng (mục tiêu 6 chỉ rule-based heuristic).
- Không sửa `documents`, `document_chunks`, worker OCR, Qdrant collection / re-index hàng loạt.
- Không thêm module nghiệp vụ mới ngoài mở rộng procurement + catalog.
- Không hard delete line item / catalog (soft delete only).

### Gợi Ý OCR (Mục Tiêu 6 — Tùy Chọn, Tham Chiếu)

- `GET /api/v1/procurements/{procurement_id}/line-item-suggestions` — read-only.
- `ProcurementLineItemSuggestionService`: parse chunk bảng rule-based; **không** auto-insert.
- Có thể bỏ qua mục tiêu 6 nếu heuristic chưa đủ tin cậy — ghi trong `PROJECT_STATUS.md`.

### Smoke (Mục Tiêu 3+)

`smoke_procurement_line_items.py`:

1. Tạo procurement (reuse fixture Phase 13).
2. POST ≥2 line items → GET list đúng thứ tự `line_number`.
3. PATCH quantity/unit_price → assert `amount` recalc.
4. DELETE (admin) → list còn đúng.
5. (Mục tiêu 7) Filter list + search với `procurement_item_name`.

Regression: `smoke_procurement_api`, `smoke_search_module_filters` sau mục tiêu 7.

### Hướng Dẫn Cho Mục Tiêu Tiếp Theo

**Mục tiêu 2:** migration `0017_procurement_line_items`, model `ProcurementLineItem`, `ProcurementLineItemRepository`.

**Mục tiêu 3:** `ProcurementLineItemService`, router nested/flat, audit, `smoke_procurement_line_items`.

**Mục tiêu 4:** migration `0018_materials_catalog`, admin CRUD + GET active, seed mẫu.

**Mục tiêu 5:** frontend line items UI + autocomplete + admin catalog page.

**Mục tiêu 6–8:** OCR suggestions (optional), search filter, regression đóng phase.

---

## Inventory / Tồn Kho MVP (Phase 19)

Trạng thái: **đã triển khai** (2026-06-10).

### Quyết Định MVP

| Hạng mục | Quyết định |
|----------|------------|
| Kho | **1 kho logic** — không multi-warehouse |
| Tồn | Bảng `stock_balances` — 1 dòng / `materials_catalog.id`, `quantity` Numeric |
| Phiếu | `stock_movements` — `movement_type` `in` \| `out`, cập nhật balance khi tạo |
| Ngưỡng | `min_stock_level` trên `materials_catalog` — cảnh báo UI, không chặn xuất |
| Liên kết mua sắm | `procurement_id` optional trên movement; UI nhập kho từ line items acceptance |
| Workflow | CRUD thủ công; soft delete movement (admin) đảo balance |
| Không làm | Workflow phê duyệt nhiều bước, HA Ollama, multi-warehouse |

### API

- `GET/POST /api/v1/stock-movements`, `GET/DELETE /api/v1/stock-movements/{id}`
- `GET /api/v1/stock-balances/{catalog_item_id}`, `GET /api/v1/stock-balances/low-stock`
- `GET /api/v1/materials-catalog/all?below_min=true` — filter tồn thấp

### Frontend

- `/stock-movements` — list + dialog tạo phiếu
- `/materials-catalog` — cột tồn, min level, badge
- Dashboard widget tồn thấp; nav **Tồn kho**
- `ProcurementLineItemsPanel` — nút nhập kho từ hồ sơ acceptance

### Smoke

`python -m app.scripts.smoke_inventory`
