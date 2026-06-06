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

Mục tiêu 3 nên thêm backend module hợp đồng theo `router -> service -> repository`:

- CRUD/filter tối thiểu trên `contract_records`.
- Permission theo RBAC hiện có.
- Audit log cho create/update/delete mềm metadata hợp đồng.
- Không sửa OCR/search core; liên kết document qua `document_id`.
