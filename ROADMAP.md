# Roadmap Phát Triển

Cập nhật lần cuối: 2026-06-05

## Nguyên Tắc

- Local/on-prem first, không dùng cloud service.
- Docker Compose first cho mọi workflow dev và smoke.
- MVP first, chỉ mở rộng khi giải quyết rõ workflow nghiệp vụ.
- Backend giữ luồng `router -> service -> repository`.
- Frontend giữ luồng `page -> composable -> service -> API`.
- Không tự đổi stack: FastAPI, PostgreSQL, Redis, Qdrant, PaddleOCR, OpenCV, Nuxt 3, TypeScript, PrimeVue, TailwindCSS, Pinia.

## Trạng Thái Hiện Tại

MVP end-to-end đã hoàn thành và đang chạy được bằng Docker Compose với các service `api`, `worker`, `web`, `postgres`, `redis`, `qdrant`.

Đã hoàn thành:
- Auth local, seed admin, cookie token frontend và RBAC nhẹ cho admin/user.
- Upload một file, nhiều file cùng văn bản và zip cùng văn bản.
- Quản lý metadata nghiệp vụ, metadata OCR tự động và metadata manual review.
- OCR/extract cho text, markdown, docx, xlsx, PDF có text nhúng, PDF/image scan bằng PaddleOCR/OpenCV và VietOCR.
- Chunking văn bản hành chính tiếng Việt theo metadata pháp lý, phụ lục, confidence và flag `requires_review`.
- Backfill chunk metadata và reindex Qdrant payload cho DB local/dev.
- Semantic search có filter metadata nghiệp vụ và filter chunk như `section_role`, `requires_review`.
- Document detail có preview source, OCR job audit, chunks filter và action đánh dấu chunk đã review.
- Dashboard có semantic search và admin review queue.
- Review queue đã có pagination `limit/offset`, total count, page count, nhảy đầu/cuối, filter và action review ngay trên queue.
- Danh sách `/documents` đã có pagination `limit/offset`, total count, sort ổn định và UI chuyển trang.
- Smoke API workflow cho auth/search/review queue/review action đã gom thành script tái chạy được.
- Worker đã claim OCR job atomic bằng database row lock để tránh nhiều worker xử lý trùng job.
- Worker đã có retry policy MVP với `max_attempts`, `failed_reason`, `next_run_at` và audit UI rõ hơn.
- Worker ops đã có endpoint queue status, smoke tổng hợp và runbook restart/failed job/backup/restore.
- Search rerank heuristic đã được tách khỏi search core sang config/service riêng.
- User audit UI cho admin xem audit log từng user.
- Smoke appendix data script đã có fixture thật và cleanup mặc định.

Giới hạn còn lại:
- Worker ops MVP đã có; lease timeout hoặc auto recovery cho job đang `ocr_running` sau khi worker crash vẫn để Phase 6 hardening nếu cần.
- Search rerank đã tách khỏi core; còn cần benchmark fixtures để đánh giá ranking lặp lại được.
- Chưa có module nghiệp vụ riêng cho hợp đồng, công văn đến/đi, quyết định hoặc phiếu vật tư.
- Chưa có bộ công cụ admin cấu hình danh mục, model status, backup/restore và ops hardening đầy đủ.

## Lộ Trình Ưu Tiên

### Phase 0 - MVP Foundation

Trạng thái: hoàn thành.

Mục tiêu: đưa hệ thống từ skeleton đến workflow web end-to-end có thể dùng để upload, OCR, chunk, search, review và audit.

Đã thực hiện:
- Khởi tạo stack Docker Compose, backend FastAPI, frontend Nuxt 3 và data services.
- Hoàn thiện auth/RBAC MVP.
- Hoàn thiện document upload, source file, preview, reprocess và metadata.
- Hoàn thiện OCR pipeline local và legal-aware chunking.
- Hoàn thiện semantic search, Qdrant payload filters và review workflow.
- Hoàn thiện review queue pagination polish ngày 2026-06-05.

Tiêu chí hoàn thành: workflow admin local có thể upload tài liệu, đợi đến searchable, search, mở document nguồn, review chunk và xem audit log.

### Phase 1 - Stabilize Core Workflows

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu: làm các workflow MVP ổn định hơn khi dữ liệu tăng lên và biến smoke thành kiểm tra có thể chạy lại.

Phạm vi:
- Documents pagination polish cho `/documents` đã hoàn thành ngày 2026-06-05.
- Smoke API auth wrapper cho review queue, semantic search và review action đã hoàn thành ngày 2026-06-05.
- Review queue UX polish đã hoàn thành ngày 2026-06-05.
- Dọn dẹp các smoke/script tạm thành script tái sử dụng được cho documents pagination, API workflow và review queue pagination.

Tiêu chí hoàn thành:
- Các list lớn có pagination ổn định, có total và không trùng item giữa các page.
- Smoke workflow login admin/user có thể chạy lại bằng command rõ ràng.
- User/admin permission smoke bao phủ các endpoint nhạy cảm.

### Phase 2 - Worker Reliability Và Operations

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu: giảm rủi ro khi chạy worker lâu dài hoặc nhiều worker trong môi trường on-prem.

Phạm vi:
- Claim OCR job atomic bằng database transaction/row lock đã hoàn thành ngày 2026-06-05.
- Chuẩn hóa retry, max attempts, failed reason và audit cho job đã hoàn thành ngày 2026-06-05.
- Thêm health/readiness liên quan worker và hàng đợi đã hoàn thành ngày 2026-06-05 bằng endpoint `/api/v1/ops/worker-queue`.
- Ghi tài liệu backup/restore PostgreSQL, Qdrant và uploaded source files đã hoàn thành ngày 2026-06-05.

Tiêu chí hoàn thành:
- Hai worker chạy song song không xử lý trùng một job.
- Job lỗi được retry/có failed state rõ ràng.
- Có smoke/command kiểm tra worker claim và retry.

### Phase 3 - Search Quality Và RAG Foundation

Trạng thái: đang ưu tiên tiếp theo.

Mục tiêu: tăng chất lượng retrieval và tạo nền tảng RAG local có citation mà không phụ thuộc cloud.

Phạm vi:
- Tách rerank heuristic khỏi logic core, đưa vào cấu hình/rule riêng đã hoàn thành ngày 2026-06-05.
- Tạo benchmark fixtures cho truy vấn vật tư, phụ lục, điều khoản, ngày ban hành và đơn vị ban hành.
- Đánh giá embedding local và rerank local nếu cần.
- Thiết kế RAG answer endpoint local-only với citation chunk/document/source page.

Tiêu chí hoàn thành:
- Có bộ benchmark search lặp lại được.
- Search result giải thích được bằng metadata/chunk citation.
- RAG nếu bắt đầu phải trả lời kèm citation, không thay thế search MVP.

### Phase 4 - Domain Modules

Trạng thái: chưa bắt đầu.

Mục tiêu: mở rộng từ kho văn bản chung sang các module nghiệp vụ thực tế của phòng vật tư.

Phạm vi ứng viên:
- Hợp đồng và phụ lục hợp đồng.
- Công văn đến/đi.
- Quyết định, thông báo, đề nghị mua sắm.
- Phiếu/đề xuất vật tư nếu cần quản lý inventory workflow.

Tiêu chí hoàn thành:
- Mỗi module có metadata riêng, filter riêng và không phá document/search core.
- UI giữ tái sử dụng component và service/composable hiện có.
- Migration có audit fields và soft delete theo quy tắc dự án.

### Phase 5 - Admin Configuration Và Governance

Trạng thái: chưa bắt đầu.

Mục tiêu: để admin cấu hình hệ thống thay vì sửa code cho các danh mục và rule cơ bản.

Phạm vi:
- Quản lý danh mục đơn vị/phòng ban, loại nghiệp vụ, loại văn bản.
- Trang trạng thái model/OCR/Qdrant.
- Cấu hình nhẹ cho threshold review, page size mặc định và rule smoke/dev.
- Mở rộng permission nếu workflow nghiệp vụ yêu cầu.

Tiêu chí hoàn thành:
- Admin thay đổi danh mục có audit log.
- Frontend lấy option từ API thay vì hardcode nhưng không làm quá phức tạp MVP.

### Phase 6 - On-Prem Production Hardening

Trạng thái: chưa bắt đầu.

Mục tiêu: chuẩn bị vận hành nội bộ on-prem một cách có kiểm soát.

Phạm vi:
- Chuẩn hóa `.env`, secret, CORS, file upload limits và log policy.
- Tài liệu backup/restore và migration runbook.
- Resource limits Docker Compose và storage volumes.
- Observability tối thiểu: health, logs, job metrics có thể xem được.

Tiêu chí hoàn thành:
- Có runbook cài đặt, nâng cấp, backup, restore và troubleshoot.
- Cấu hình production nội bộ không dùng default secret/admin password.
