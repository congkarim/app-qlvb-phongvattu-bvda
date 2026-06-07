# Domain Module Decision

Cập nhật lần cuối: 2026-06-07 (Phase 13 mục tiêu 1 — thiết kế procurement)

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

## Hướng Dẫn Cho Mục Tiêu Tiếp Theo

**Mục tiêu 2** nên tạo migration `procurement_records` + model SQLAlchemy + seed catalog `business_type=procurement` theo schema/index ở trên.

**Mục tiêu 3** thêm `ProcurementRepository`, `ProcurementService`, router và `smoke_procurement_api`.

**Mục tiêu 4–5** thêm frontend `/procurements` và card liên kết document detail theo `page -> composable -> service -> API`.
