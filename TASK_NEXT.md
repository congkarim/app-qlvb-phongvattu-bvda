# Kế Hoạch Task Tiếp Theo

Cập nhật lần cuối: 2026-06-05

Tài liệu này bám theo `ROADMAP.md` và trạng thái đã ghi trong `PROJECT_STATUS.md`. Mục ưu tiên hiện tại là ổn định core workflow sau khi MVP và review queue pagination đã hoàn thành.

## Task Vừa Hoàn Thành

Queue pagination polish: hoàn thành ngày 2026-06-05.

Kết quả chính:
- Backend `GET /api/v1/documents/chunks/review-queue` trả `items`, `total`, `limit`, `offset`.
- Repository có count matching cùng filter `section_role`, `document_id`, `max_confidence`.
- Query queue có sort ổn định theo confidence, `updated_at` và `DocumentChunk.id`.
- Dashboard admin hiển thị tổng số item, khoảng item hiện tại, nút `Trước/Sau`, giữ filter khi chuyển trang và refresh hợp lý sau action `Đã review`.
- Frontend vẫn giữ đúng luồng `page -> composable -> service -> API`.

Đã kiểm tra:
- Backend compile pass.
- Frontend build pass, chỉ còn warning chunk PrimeVue lớn như trước.
- Appendix smoke pass.
- Pagination smoke pass với hai page không trùng item.
- User forbidden smoke pass với review queue trả `403`.

## Ưu Tiên 1 - Documents Pagination Polish

Trạng thái: đề xuất làm tiếp theo.

Mục tiêu:
- Thay limit cố định trên `/documents` bằng pagination có total count để danh sách văn bản dùng được khi data tăng.
- Giữ luồng frontend `page -> composable -> service -> API`.
- Giữ backend `router -> service -> repository`.

Phạm vi backend:
- Mở rộng schema response danh sách document thành object có `items`, `total`, `limit`, `offset`.
- Giữ các filter/search/sort hiện có của danh sách document.
- Thêm repository count document matching đúng cùng filter với list.
- Tách helper filter nếu cần để list/count không lệch logic.
- Thêm sort tie-breaker bằng `Document.id` để pagination ổn định.
- Giữ endpoint permission hiện có, không thêm migration nếu không cần.

Phạm vi frontend:
- Cập nhật type response document list.
- Cập nhật `document.service.ts` nhận response pagination.
- Cập nhật composable quản lý `documents`, `documentsTotal`, `documentsLimit`, `documentsOffset`.
- Cập nhật page `/documents` để hiển thị tổng số, khoảng item, nút trang trước/sau hoặc paginator PrimeVue nếu phù hợp.
- Reset offset về `0` khi đổi search/filter/sort.
- Giữ refresh action và empty/loading/error state hiện có.

Tiêu chí chấp nhận:
- Danh sách document page 1/page 2 không trùng item khi dữ liệu đủ lớn.
- Search/filter/sort vẫn hoạt động sau khi thêm pagination.
- UI không gọi API trực tiếp trong component ngoài service/composable hiện có.
- Không phá document detail, upload, search dashboard.

Kiểm tra cần chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/document.py apps/api/app/repositories/document_repository.py apps/api/app/services/document_service.py apps/api/app/routers/documents.py
docker compose run --rm --no-deps web npm run build
python3 <documents pagination smoke script>
git diff --check
```

## Ưu Tiên 2 - Smoke API Auth Wrapper

Trạng thái: đề xuất sau documents pagination.

Mục tiêu:
- Chuyển các smoke HTTP inline thành script tái chạy được, có login admin/user và cleanup rõ ràng.
- Giảm rủi ro regression cho review queue, semantic search và review action.

Phạm vi:
- Tạo script smoke API workflow trong `apps/api/app/scripts/`.
- Dùng admin local để login và lấy token.
- Tạo user thường tạm nếu cần để kiểm tra permission.
- Seed document/chunk smoke tối thiểu hoặc tái sử dụng appendix fixture hiện có.
- Kiểm tra review queue admin thành công và user thường bị `403`.
- Kiểm tra semantic search với filter cơ bản và filter `section_role=appendix`.
- Kiểm tra action review chunk cập nhật DB và Qdrant payload.
- Cleanup user/document/chunk/Qdrant point sau khi chạy, có option `--keep-data` nếu cần debug UI.

Tiêu chí chấp nhận:
- Một command smoke có thể chạy lại trên Docker Compose đang active.
- Script fail fast với error message rõ endpoint nào lỗi.
- Dữ liệu smoke không để lại rác khi chạy mặc định.

Kiểm tra cần chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/scripts/smoke_api_workflows.py
docker compose exec -T api python -m app.scripts.smoke_api_workflows
git diff --check
```

## Ưu Tiên 3 - Review Queue UX Polish

Trạng thái: tùy chọn, làm khi queue nhiều trang cần thao tác nhanh hơn.

Mục tiêu:
- Cải thiện thao tác admin trên queue dài mà không làm phức tạp dashboard.

Phạm vi:
- Đánh giá UI hiện tại `Trước/Sau` có đủ dùng không.
- Nếu cần, thay bằng PrimeVue paginator hoặc thêm current page/page count.
- Giữ filter queue hiện có: tất cả, phụ lục, unknown, confidence thấp, document id.
- Đảm bảo action `Đã review` không đẩy admin về sai page.

Tiêu chí chấp nhận:
- Admin biết đang ở page nào và tổng số item còn lại.
- Chuyển trang không mất filter.
- UI compact, không tạo card lồng nhau.

Kiểm tra cần chạy:

```bash
docker compose run --rm --no-deps web npm run build
python3 <review queue pagination smoke script>
git diff --check
```

## Phase 2 - Worker Reliability Và Operations

Trạng thái: chưa bắt đầu.

Mục tiêu:
- Làm OCR worker an toàn hơn khi chạy lâu dài hoặc chạy nhiều worker.

Kế hoạch chi tiết:
- Khảo sát hiện trạng worker polling pending job và repository update job status.
- Thêm cơ chế claim atomic bằng transaction/row lock để tránh hai worker xử lý cùng job.
- Chuẩn hóa `attempts`, retry policy, failed reason và job audit.
- Thêm smoke hoặc integration check với hai worker/process nếu khả thi.
- Viết runbook ngắn cho restart worker, job failed và reprocess.

Tiêu chí chấp nhận:
- Hai worker song song không xử lý trùng một OCR job.
- Job failed có error rõ và không bị lặp vô hạn.
- Reprocess vẫn tạo job đúng và detail page vẫn polling đúng status.

## Phase 3 - Search Quality Và RAG Foundation

Trạng thái: chưa bắt đầu.

Mục tiêu:
- Tăng chất lượng retrieval và chuẩn bị RAG local có citation.

Kế hoạch chi tiết:
- Trích xuất các heuristic rerank hardcoded thành module/rule riêng.
- Tạo bộ benchmark query fixture cho vật tư, phụ lục, điều khoản, ngày ban hành và đơn vị ban hành.
- Thêm command chạy benchmark search local và report top-k.
- Đánh giá embedding local/rerank local nếu cần, không dùng cloud.
- Thiết kế API RAG local-only sau khi benchmark search ổn định.

Tiêu chí chấp nhận:
- Search core không trộn các rule mẫu hardcoded khó maintain.
- Benchmark có thể chạy lại và so sánh thay đổi ranking.
- Câu trả lời RAG nếu thêm phải có citation chunk/document/source.

## Phase 4 - Domain Modules

Trạng thái: chưa bắt đầu.

Mục tiêu:
- Mở rộng từ document repository chung sang các module nghiệp vụ của phòng vật tư.

Kế hoạch chi tiết:
- Chọn một module đầu tiên có giá trị cao nhất, ví dụ hợp đồng/phụ lục hợp đồng hoặc công văn đến/đi.
- Định nghĩa metadata riêng nhưng vẫn liên kết document core.
- Tạo migration có UUID primary key, audit fields và soft delete.
- Thêm backend theo `router -> service -> repository`.
- Thêm frontend theo `page -> composable -> service -> API`.
- Tái sử dụng component list/filter/detail nếu có thể.

Tiêu chí chấp nhận:
- Module mới không phá upload/OCR/search core.
- Metadata module có thể filter/search được.
- UI có workflow nghiệp vụ rõ, không chỉ là landing page.

## Phase 5 - Admin Configuration Và Governance

Trạng thái: chưa bắt đầu.

Mục tiêu:
- Để admin quản lý danh mục và cấu hình nhẹ không cần sửa code.

Kế hoạch chi tiết:
- Thiết kế danh mục cần có: đơn vị/phòng ban, loại nghiệp vụ, loại văn bản.
- Thêm CRUD admin có audit log.
- Cập nhật frontend option lấy từ API thay vì hardcode cho các field phù hợp.
- Thêm trang status tối thiểu cho OCR/model/Qdrant.
- Nếu cần, mở rộng permission nhưng giữ RBAC đơn giản.

Tiêu chí chấp nhận:
- Admin thay đổi danh mục có audit log.
- UI form dùng option từ API và vẫn có fallback hợp lý.
- Không biến admin config thành framework phức tạp.

## Phase 6 - On-Prem Production Hardening

Trạng thái: chưa bắt đầu.

Mục tiêu:
- Chuẩn bị vận hành nội bộ on-prem có kiểm soát.

Kế hoạch chi tiết:
- Chuẩn hóa `.env`, secret, CORS và default admin password policy.
- Tài liệu storage volumes cho PostgreSQL, Qdrant và uploads.
- Viết backup/restore runbook.
- Thêm health/readiness check cần thiết.
- Kiểm tra upload limits, log policy và resource limits Docker Compose.

Tiêu chí chấp nhận:
- Cài đặt mới không dùng secret/password mặc định trong production nội bộ.
- Có tài liệu backup/restore và troubleshoot.
- Health check phân biệt service sống với service sẵn sàng xử lý workflow.
