# Roadmap Phát Triển

Cập nhật lần cuối: 2026-06-06

## Nguyên Tắc

- Local/on-prem first, không dùng cloud service.
- Docker Compose first cho mọi workflow dev và smoke.
- MVP first, chỉ mở rộng khi giải quyết rõ workflow nghiệp vụ.
- Backend giữ luồng `router -> service -> repository`.
- Frontend giữ luồng `page -> composable -> service -> API`.
- Không tự đổi stack: FastAPI, PostgreSQL, Redis, Qdrant, PaddleOCR, OpenCV, Nuxt 3, TypeScript, PrimeVue, TailwindCSS, Pinia.

## Trạng Thái Hiện Tại

**Lộ trình Phase 0–7 đã hoàn thành.** Hệ thống có thể chạy on-prem bằng Docker Compose với các service `api`, `worker`, `web`, `postgres`, `redis`, `qdrant`.

**Phase hiện tại: Phase 10 - Module Quyết Định Và Thông Báo** (checklist chi tiết trong `TASK_NEXT.md`).

Đã hoàn thành:
- Auth local, seed admin, cookie token frontend và RBAC nhẹ cho admin/user.
- Upload một file, nhiều file cùng văn bản, zip cùng văn bản; upload policy và giới hạn kích thước có thể cấu hình.
- Quản lý metadata nghiệp vụ, metadata OCR tự động và metadata manual review.
- OCR/extract cho text, markdown, docx, xlsx, PDF có text nhúng, PDF/image scan bằng PaddleOCR/OpenCV và VietOCR.
- Chunking văn bản hành chính tiếng Việt theo metadata pháp lý, phụ lục, confidence và flag `requires_review`.
- Semantic search có filter metadata nghiệp vụ, filter chunk như `section_role`, `requires_review`, và filter metadata hợp đồng (`contract_number`, `supplier_name`, `contract_status`).
- RAG foundation local-only: endpoint `POST /api/v1/search/answer` trả lời extractive kèm citation.
- Document detail có preview source, OCR job audit, chunks filter và action đánh dấu chunk đã review.
- Dashboard có semantic search, RAG Q&A extractive kèm citation, admin review queue có pagination/filter.
- Module hợp đồng MVP: backend `contract_records`, API CRUD, frontend `/contracts`; liên kết hai chiều với document detail.
- Module công văn đến/đi MVP: backend `dispatch_records`, API CRUD, frontend `/dispatches`; liên kết hai chiều với document detail.
- Admin catalog MVP: departments, business_type, document_type qua Catalog API; trang `/status` cho OCR/model/Qdrant/worker queue.
- Worker claim atomic, retry policy, queue status endpoint và smoke worker operations.
- On-prem hardening: env/secret/CORS guard, backup/restore runbook, health/readiness, log policy, compose resource limits.
- Worker lease timeout, stale-job recovery, ops endpoint job kẹt, runbook upgrade Alembic production, smoke worker stale recovery.

Giới hạn còn lại (ưu tiên Phase 10):
- Chưa có module nghiệp vụ thứ ba (quyết định/thông báo).
- Chưa có LLM/generator nội bộ nâng cao; RAG hiện extractive từ chunk truy xuất.

## Lộ Trình Ưu Tiên

### Phase 0 - MVP Foundation

Trạng thái: hoàn thành.

Mục tiêu: đưa hệ thống từ skeleton đến workflow web end-to-end có thể dùng để upload, OCR, chunk, search, review và audit.

Tiêu chí hoàn thành: workflow admin local có thể upload tài liệu, đợi đến searchable, search, mở document nguồn, review chunk và xem audit log.

### Phase 1 - Stabilize Core Workflows

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu: làm các workflow MVP ổn định hơn khi dữ liệu tăng lên và biến smoke thành kiểm tra có thể chạy lại.

Tiêu chí hoàn thành:
- Các list lớn có pagination ổn định, có total và không trùng item giữa các page.
- Smoke workflow login admin/user có thể chạy lại bằng command rõ ràng.
- User/admin permission smoke bao phủ các endpoint nhạy cảm.

### Phase 2 - Worker Reliability Và Operations

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu: giảm rủi ro khi chạy worker lâu dài hoặc nhiều worker trong môi trường on-prem.

Tiêu chí hoàn thành:
- Hai worker chạy song song không xử lý trùng một job.
- Job lỗi được retry/có failed state rõ ràng.
- Có smoke/command kiểm tra worker claim và retry.

### Phase 3 - Search Quality Và RAG Foundation

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: tăng chất lượng retrieval và tạo nền tảng RAG local có citation mà không phụ thuộc cloud.

Tiêu chí hoàn thành:
- Có bộ benchmark search lặp lại được.
- Search result giải thích được bằng metadata/chunk citation.
- RAG endpoint trả lời kèm citation, không thay thế search MVP.

### Phase 4 - Domain Modules

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: mở rộng từ kho văn bản chung sang module nghiệp vụ thực tế của phòng vật tư.

Đã thực hiện:
- Module đầu tiên: **Hợp đồng và phụ lục hợp đồng** (`contract_records`, API, `/contracts`).

Tiêu chí hoàn thành:
- Module có metadata riêng, filter riêng và không phá document/search core.
- UI giữ tái sử dụng component và service/composable hiện có.
- Migration có audit fields và soft delete theo quy tắc dự án.

### Phase 5 - Admin Configuration Và Governance

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: để admin cấu hình hệ thống thay vì sửa code cho các danh mục và rule cơ bản.

Tiêu chí hoàn thành:
- Admin thay đổi danh mục có audit log.
- Frontend lấy option từ API thay vì hardcode.
- Admin xem được trạng thái OCR/model/Qdrant tối thiểu.

### Phase 6 - On-Prem Production Hardening

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: chuẩn bị vận hành nội bộ on-prem một cách có kiểm soát.

Tiêu chí hoàn thành:
- Có runbook cài đặt, backup, restore, troubleshoot, log policy và upload/resource limits.
- Cấu hình production nội bộ không dùng default secret/admin password.
- Health/readiness và observability tối thiểu đủ cho vận hành on-prem.

### Phase 7 - Domain Integration Và Module Mở Rộng

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: tăng giá trị nghiệp vụ thực tế sau khi nền tảng on-prem đã sẵn sàng, bắt đầu từ module hợp đồng hiện có và mở module nghiệp vụ thứ hai.

Phạm vi đề xuất:
- **Liên kết hợp đồng ↔ document core**: từ `/documents/[id]` mở metadata hợp đồng nếu có; từ `/contracts` drill-down sang document/chunks/search liên quan.
- **Search filter theo metadata hợp đồng**: filter dashboard/search theo nhà cung cấp, trạng thái, số hợp đồng khi phù hợp MVP.
- **Module nghiệp vụ thứ hai**: chọn **công văn đến/đi** làm ứng viên ưu tiên (metadata riêng, CRUD, list/filter UI theo pattern `contracts`).
- Thiết kế quyết định module mới trong `docs/DOMAIN_MODULE_DECISION.md` trước khi code.

Không làm trong phase này:
- Inventory/procurement workflow nhiều bước.
- LLM/generator nội bộ nâng cao.
- Thay đổi stack hoặc thêm cloud service.

Tiêu chí hoàn thành:
- Document detail và contract module liên kết hai chiều rõ ràng.
- Có ít nhất một filter search/dashboard dùng metadata hợp đồng.
- Module công văn đến/đi có schema, API, UI MVP và smoke script tái chạy được.
- Không phá upload/OCR/search/review workflow hiện có.

### Phase 8 - Worker Resilience Và Production Upgrade

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: giảm rủi ro vận hành lâu dài khi worker crash hoặc khi nâng cấp phiên bản trên môi trường nội bộ.

Tiêu chí hoàn thành:
- Job `ocr_running` bị kẹt có cơ chế phát hiện và recovery có kiểm soát.
- Có runbook upgrade/migration có thể làm theo trên on-prem.
- Smoke worker recovery pass trên Docker Compose.

### Phase 9 - RAG UX Và Search Nâng Cao

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu: đưa RAG foundation từ API backend lên workflow người dùng và cải thiện search theo dữ liệu thật.

Đã thực hiện:
- Panel **Hỏi đáp (RAG)** trên `/dashboard` (`useRagAnswer`, `RagAnswerPanel`, `POST /search/answer`).
- Fallback `insufficient_evidence` phân biệt rõ trên UI; citation quote + link document.
- Runbook `docs/RAG_ANSWER_RUNBOOK.md` và smoke `smoke_rag_answer` tái chạy được.

Tiêu chí hoàn thành:
- User có thể hỏi–đáp trên web với citation rõ ràng.
- Fallback `insufficient_evidence` hiển thị đúng trên UI.
- Benchmark hoặc smoke RAG answer có thể chạy lại.

### Phase 10 - Module Quyết Định Và Thông Báo

Trạng thái: đang làm (bắt đầu 2026-06-06).

Mục tiêu: mở module nghiệp vụ thứ ba cho quyết định/thông báo nội bộ theo pattern hợp đồng và công văn.

Phạm vi đề xuất:
- Thiết kế scope trong `docs/DOMAIN_MODULE_DECISION.md` trước khi code.
- Schema `decision_records` (hoặc tên tương đương), API CRUD, UI `/decisions`, smoke script.
- Liên kết hai chiều với document core; search/RAG tiếp tục dựa trên chunk/document.

Không làm trong phase này:
- Inventory/procurement workflow nhiều bước.
- LLM local nặng hoặc cloud API.

Tiêu chí hoàn thành:
- Module có metadata riêng, filter list và không phá document/search core.
- UI theo `page -> composable -> service -> API`; smoke tái chạy được.

## Ghi Chú Lập Kế Hoạch

- `TASK_NEXT.md` chỉ chứa checklist phase đang làm (hiện Phase 10); lịch sử phase đã xong nằm trong `PROJECT_STATUS.md`.
- Con trỏ thực thi: `TASK_NEXT.md` → `PROJECT_STATUS.md` → commit sau mỗi mục tiêu (skill `project-git-manager`).
- Ưu tiên MVP và maintainability; mỗi module nghiệp vụ mới phải có quyết định scope trong `docs/DOMAIN_MODULE_DECISION.md`.
- Mỗi mục tiêu Phase 9 khi hoàn thành phải auto commit theo quy tắc trong `TASK_NEXT.md`.
