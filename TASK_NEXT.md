# Kế Hoạch Task Tiếp Theo

Cập nhật lần cuối: 2026-06-06

Tài liệu này là checklist thực thi tuần tự bám theo `ROADMAP.md`. Khi người dùng nói `thực hiện TASK_NEXT.md`, agent phải bắt đầu từ mục đầu tiên có trạng thái `chưa làm` hoặc `đang làm`, không nhảy sang phase sau khi phase hiện tại chưa đạt tiêu chí hoàn thành.

## Quy Tắc Thực Thi Bắt Buộc

- Trước khi bắt đầu bất kỳ mục tiêu nào: đọc lại `ROADMAP.md`, `PROJECT_STATUS.md` và `TASK_NEXT.md`.
- Chỉ làm một mục tiêu nhỏ tại một thời điểm.
- Xong mục tiêu nào phải kiểm tra tiêu chí chấp nhận của mục tiêu đó, cập nhật `PROJECT_STATUS.md` và `TASK_NEXT.md`.
- Sau khi xong từng mục tiêu: đọc lại `ROADMAP.md` để xác nhận ưu tiên còn đúng trước khi lập kế hoạch cho mục tiêu kế tiếp.
- Sau khi xong một phase: đọc lại toàn bộ `ROADMAP.md`, cập nhật trạng thái phase trong `TASK_NEXT.md`, rồi mới mở khóa phase kế tiếp.
- Không thực hiện Phase 2 khi Phase 1 chưa hoàn thành; tương tự với các phase sau.
- Giữ đúng stack cố định và kiến trúc:
  - Backend: `router -> service -> repository`.
  - Frontend: `page -> composable -> service -> API`.
- Khi hoàn thành task, dùng skill `project-git-manager` để kiểm tra repo, cập nhật tài liệu trạng thái và commit thay đổi liên quan nếu repo đã sẵn sàng.

## Con Trỏ Hiện Tại

Phase hiện tại: Phase 5 - Admin Configuration Và Governance.

Mục tiêu tiếp theo phải làm: Phase 5 / Mục tiêu 3 - Frontend Dùng Option Từ API.

Điều kiện chuyển sang mục tiêu kế tiếp:
- Mục tiêu hiện tại pass tiêu chí chấp nhận.
- Các kiểm tra bắt buộc đã chạy hoặc lý do chưa chạy được đã ghi rõ.
- `ROADMAP.md` đã được đọc lại sau khi hoàn thành mục tiêu.
- `TASK_NEXT.md` đã được cập nhật để đánh dấu mục tiêu hoàn thành và chọn mục tiêu tiếp theo.

## Phase 0 - MVP Foundation

Trạng thái: hoàn thành.

Mục tiêu đã hoàn thành:
- Docker Compose stack cho `api`, `worker`, `web`, `postgres`, `redis`, `qdrant`.
- Auth local, seed admin, cookie token frontend và RBAC nhẹ.
- Upload một file, nhiều file cùng văn bản và zip cùng văn bản.
- OCR/extract local cho text, markdown, docx, xlsx, PDF text, PDF/image scan.
- Chunking văn bản hành chính tiếng Việt, metadata chunk và review flag.
- Semantic search với Qdrant payload filters.
- Document detail, source preview, OCR audit, chunk filter và action review chunk.
- Dashboard semantic search và admin review queue.
- Review queue pagination, filter và action review từ queue.
- User audit UI.
- Appendix smoke data script có fixture thật và cleanup mặc định.

Tiêu chí phase: đã đạt.

Ghi chú thực thi:
- Không quay lại Phase 0 trừ khi `ROADMAP.md` thay đổi hoặc phát hiện regression ảnh hưởng MVP foundation.

## Phase 1 - Stabilize Core Workflows

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu phase: làm các workflow MVP ổn định hơn khi dữ liệu tăng lên và biến smoke thành kiểm tra có thể chạy lại.

Điều kiện hoàn thành phase:
- `/documents` có pagination ổn định, có total và không trùng item giữa các page.
- Smoke workflow login admin/user có thể chạy lại bằng command rõ ràng.
- User/admin permission smoke bao phủ endpoint nhạy cảm liên quan review queue, semantic search và review action.
- Các script smoke tạm quan trọng đã được gom thành script tái sử dụng hoặc có lý do giữ lại rõ ràng.
- Đã đọc lại `ROADMAP.md` và cập nhật kế hoạch Phase 2 trước khi chuyển phase.

### Mục Tiêu 1 - Documents Pagination Polish

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu:
- Thay limit cố định trên `/documents` bằng pagination có total count để danh sách văn bản dùng được khi dữ liệu tăng.
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

Kết quả:
- Backend `GET /api/v1/documents` trả `items`, `total`, `limit`, `offset`.
- Repository dùng chung filter helper cho list/count và sort ổn định bằng `Document.id`.
- Frontend `/documents` hiển thị tổng số, khoảng item hiện tại và nút `Trước/Sau`.
- Search/filter/sort reset về page đầu; refresh giữ page hiện tại.
- Thêm script `python -m app.scripts.smoke_documents_pagination`.

Kiểm tra cần chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/document.py apps/api/app/repositories/document_repository.py apps/api/app/services/document_service.py apps/api/app/routers/documents.py
docker compose run --rm --no-deps web npm run build
python3 <documents pagination smoke script>
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Đã chuyển con trỏ hiện tại sang `Phase 1 / Mục tiêu 2`.

### Mục Tiêu 2 - Smoke API Auth Wrapper

Trạng thái: hoàn thành ngày 2026-06-05.

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
- Permission smoke bao phủ admin/user cho review queue và review action.

Kết quả:
- Thêm script `python -m app.scripts.smoke_api_workflows`.
- Script login admin/user qua HTTP API.
- Script seed document/chunk smoke tối thiểu, index Qdrant payload và cleanup mặc định.
- Admin review queue pass; user thường review queue nhận `403`.
- Semantic search cơ bản và filter `section_role=appendix` pass.
- Admin review action cập nhật DB và Qdrant payload; user thường review action nhận `403`.

Kiểm tra cần chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/scripts/smoke_api_workflows.py
docker compose exec -T api python -m app.scripts.smoke_api_workflows
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Đã chuyển con trỏ hiện tại sang `Phase 1 / Mục tiêu 3`.

### Mục Tiêu 3 - Review Queue UX Polish

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu:
- Cải thiện thao tác admin trên queue dài nếu UI hiện tại chưa đủ rõ khi có nhiều trang.
- Không làm dashboard phức tạp hoặc phá bố cục compact.

Phạm vi:
- Đánh giá UI hiện tại `Trước/Sau` có đủ dùng không sau khi smoke workflow đã ổn định.
- Nếu cần, thay bằng PrimeVue paginator hoặc thêm current page/page count.
- Giữ filter queue hiện có: tất cả, phụ lục, unknown, confidence thấp, document id.
- Đảm bảo action `Đã review` không đẩy admin về sai page.
- Không tạo card lồng nhau.

Tiêu chí chấp nhận:
- Admin biết đang ở page nào và tổng số item còn lại.
- Chuyển trang không mất filter.
- Action review xong refresh đúng page hoặc lùi page hợp lý khi page rỗng.
- UI compact, không thêm text hướng dẫn dư thừa trong app.

Kết quả:
- Dashboard review queue hiển thị khoảng item, tổng số item và `Trang X/Y`.
- Thêm nút nhảy trang đầu/cuối dạng icon, giữ nút `Trước/Sau`.
- Offset/limit được đồng bộ theo response API.
- Action `Đã review` vẫn refresh page hiện tại hoặc lùi page khi page rỗng.
- Thêm script `python -m app.scripts.smoke_review_queue_pagination`.

Kiểm tra cần chạy:

```bash
docker compose run --rm --no-deps web npm run build
python3 <review queue pagination smoke script>
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Phase 1 đã đạt điều kiện hoàn thành, đã đánh dấu Phase 1 `hoàn thành` và mở khóa Phase 2.

## Phase 2 - Worker Reliability Và Operations

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu phase: giảm rủi ro khi chạy worker lâu dài hoặc nhiều worker trong môi trường on-prem.

Điều kiện bắt đầu:
- Phase 1 đã hoàn thành.
- Đã đọc lại `ROADMAP.md` sau Phase 1.
- `TASK_NEXT.md` đã cập nhật con trỏ sang `Phase 2 / Mục tiêu 1`.

### Mục Tiêu 1 - Khảo Sát Worker Và Job Lifecycle

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu:
- Hiểu rõ worker hiện đang poll pending job, update status, retry và ghi lỗi như thế nào.

Phạm vi:
- Đọc worker loop, OCR job repository/service và các endpoint reprocess.
- Xác định nơi cần transaction/row lock.
- Ghi lại trạng thái hiện có của `attempts`, `status`, `error_message`, `job_type`, `reason`.

Tiêu chí chấp nhận:
- Có ghi chú kỹ thuật trong `TASK_NEXT.md` hoặc `PROJECT_STATUS.md` về điểm cần sửa.
- Chưa thay đổi behavior lớn trước khi nắm rõ lifecycle.

Kết quả khảo sát:
- Worker loop: `apps/worker/runner.py` gọi `run_forever(SessionLocal)`, mỗi vòng tạo session mới, `OCRWorker.run_once()` xử lý tối đa 1 job, không có job thì sleep 5 giây.
- Job claim hiện tại: `OCRJobRepository.get_next_pending_job()` chỉ select job `pending` cũ nhất, không lock row, không `SKIP LOCKED`, không đổi status trong cùng transaction.
- Điểm race chính: `run_once()` lấy job rồi `process_job()` mới set `ocr_running` và commit. Nhiều worker có thể lấy cùng pending job trước khi worker đầu commit.
- Upload một file, multi-file và zip tạo job `job_type='ocr'`, `status='pending'`, document `ocr_pending`.
- Reprocess thủ công và thay đổi source file tạo job `job_type='reprocess'`, `status='pending'`, `reason`, document `reprocess_pending`.
- Active job hiện chỉ tính status `pending` và `ocr_running`; không có status riêng `reprocess_running` trong job table, reprocess chỉ thể hiện qua `job_type`.
- Worker success path: document `ocr_running/reprocess_running -> chunking -> searchable`, job `completed`, set `completed_at`.
- Worker error path: job `failed`, `error_message=str(exc)`; OCR thường đưa document `failed`, reprocess đưa document về trạng thái trước đó nếu có; source file chưa completed bị set `failed`.
- Chưa có retry policy, `max_attempts`, delayed retry, failed reason taxonomy, worker id/lease hoặc timeout cho job đang chạy.
- Health hiện chỉ có `/health` đơn giản, chưa có worker/queue readiness.

Điểm cần sửa ở mục tiêu 2:
- Thêm repository method claim atomic, ví dụ transaction `SELECT ... FOR UPDATE SKIP LOCKED` trên job `pending`, order `created_at asc`, limit 1.
- Trong cùng transaction claim, set job `ocr_running`, tăng `attempts`, set `started_at`, clear/giữ `error_message` theo policy, rồi commit trước khi xử lý OCR dài.
- `OCRWorker.run_once()` nên gọi claim method thay vì `get_next_pending_job()` + set status tách rời.
- Giữ `has_active_job()` hoạt động với status active hiện tại để không phá upload/reprocess.

### Mục Tiêu 2 - Atomic Claim OCR Job

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu:
- Đảm bảo nhiều worker song song không xử lý trùng một OCR job.

Phạm vi:
- Thêm claim job atomic bằng database transaction/row lock.
- Chỉ một worker chuyển job từ pending sang running.
- Giữ reprocess và job audit hiện có hoạt động.

Tiêu chí chấp nhận:
- Hai worker/process song song không claim cùng job.
- Không làm mất pending job khi worker dừng giữa chừng.

Kết quả:
- Thêm `OCRJobRepository.claim_next_pending_job()` để select job `pending` cũ nhất bằng `FOR UPDATE SKIP LOCKED`.
- Trong cùng transaction claim, job được đổi sang `ocr_running`, tăng `attempts`, set `started_at` và clear `error_message`.
- `OCRWorker.run_once()` dùng claim method và commit claim trước khi xử lý OCR dài.
- `process_job()` không còn tự claim job lại, chỉ tiếp tục success/error lifecycle hiện có.
- Thêm script `python -m app.scripts.smoke_worker_claim_atomic` để kiểm tra hai session song song không claim cùng một job.

Kiểm tra đã chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/repositories/document_repository.py apps/api/app/workers/ocr_worker.py apps/api/app/scripts/smoke_worker_claim_atomic.py
docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_claim_atomic
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Đã chuyển con trỏ hiện tại sang `Phase 2 / Mục tiêu 3`.

### Mục Tiêu 3 - Retry, Failed Reason Và Audit

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu:
- Chuẩn hóa retry, max attempts, failed reason và audit cho job lỗi.

Phạm vi:
- Xác định retry policy MVP.
- Cập nhật status/error rõ ràng.
- Đảm bảo job lỗi không lặp vô hạn.

Tiêu chí chấp nhận:
- Job failed có error rõ.
- Retry count có giới hạn.
- Detail page vẫn hiển thị audit job dễ hiểu.

Kết quả:
- Migration `0010_ocr_job_retry_fields` thêm `max_attempts`, `failed_reason`, `next_run_at` và index theo `status/next_run_at/created_at`.
- `OCRJobRepository.claim_next_pending_job()` chỉ claim job `pending` khi `next_run_at` rỗng hoặc đã tới hạn.
- Worker phân loại lỗi MVP:
  - Không retry: document không tồn tại, file upload mất, unsupported format, empty content, empty chunks, cấu hình OCR/embedding không hợp lệ.
  - Retry: lỗi runtime còn lại với `failed_reason=processing_error`.
- Khi còn lượt, job quay về `pending`, set `next_run_at`, document quay về pending tương ứng và source file chưa completed được reset `pending`.
- Khi hết lượt hoặc lỗi không retry, job chuyển `failed`, ghi `error_message`, `failed_reason`, `completed_at` và clear `next_run_at`.
- Detail page hiển thị `attempts/max_attempts`, `failed_reason` và thời điểm `next_run_at`.
- Thêm script `python -m app.scripts.smoke_worker_retry_policy`.

Kiểm tra đã chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/document.py apps/api/app/schemas/document.py apps/api/app/repositories/document_repository.py apps/api/app/workers/ocr_worker.py apps/api/app/scripts/smoke_worker_retry_policy.py apps/api/alembic/versions/0010_ocr_job_retry_fields.py
docker compose stop worker
docker compose exec -T api alembic upgrade head
docker compose exec -T api python -m app.scripts.smoke_worker_retry_policy
docker compose exec -T api python -m app.scripts.smoke_worker_claim_atomic
docker compose run --rm --no-deps web npm run build
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Đã chuyển con trỏ hiện tại sang `Phase 2 / Mục tiêu 4`.

### Mục Tiêu 4 - Worker Smoke Và Ops Runbook

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu:
- Có command kiểm tra worker claim/retry và hướng dẫn vận hành cơ bản.

Phạm vi:
- Thêm smoke hoặc integration check với hai worker/process nếu khả thi.
- Viết runbook ngắn cho restart worker, job failed và reprocess.
- Ghi tài liệu backup/restore PostgreSQL, Qdrant và uploaded source files nếu chưa chuyển sang Phase 6.

Tiêu chí chấp nhận:
- Có smoke/command kiểm tra worker claim hoặc retry.
- Có tài liệu thao tác khi job lỗi.

Kết quả:
- Thêm endpoint admin-only `GET /api/v1/ops/worker-queue` theo `router -> service -> repository`.
- Endpoint trả counters: `pending_ready`, `pending_delayed`, `running`, `failed`, `completed`, `active`.
- Thêm script `python -m app.scripts.smoke_worker_operations` để chạy lại atomic claim smoke, retry policy smoke và kiểm tra endpoint ops.
- Thêm `docs/WORKER_OPS_RUNBOOK.md` cho kiểm tra queue, smoke worker, restart worker, xem log, xử lý job failed/reprocess và backup/restore PostgreSQL, Qdrant, uploaded source files.
- Cập nhật `README.md` link tới runbook.

Kiểm tra đã chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/main.py apps/api/app/repositories/document_repository.py apps/api/app/schemas/ops.py apps/api/app/services/ops_service.py apps/api/app/routers/ops.py apps/api/app/scripts/smoke_worker_operations.py
docker compose stop worker
docker compose exec -T api python -m app.scripts.smoke_worker_operations
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Phase 2 đã đạt điều kiện hoàn thành, đã đánh dấu Phase 2 `hoàn thành` và mở khóa Phase 3.

Điều kiện hoàn thành Phase 2:
- Hai worker chạy song song không xử lý trùng một job.
- Job lỗi được retry/có failed state rõ ràng.
- Có smoke/command kiểm tra worker claim và retry.
- Đã đọc lại `ROADMAP.md` trước khi mở Phase 3.

## Phase 3 - Search Quality Và RAG Foundation

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu phase: tăng chất lượng retrieval và tạo nền tảng RAG local có citation, không phụ thuộc cloud.

### Mục Tiêu 1 - Tách Rerank Heuristic

Trạng thái: hoàn thành ngày 2026-06-05.

Mục tiêu:
- Tách rerank heuristic hardcoded khỏi logic core.

Phạm vi:
- Tìm heuristic hiện tại theo cụm từ mẫu.
- Chuyển sang module/rule/config riêng.
- Giữ kết quả search MVP không regression rõ ràng.

Tiêu chí chấp nhận:
- Search core không trộn rule mẫu khó maintain.
- Rule có thể chỉnh mà không phải sửa nhiều lớp service.

Kết quả:
- Thêm `SearchRerankService` và `SearchRerankConfig` để chứa rerank scoring, keyword phrase scoring và weak-match detection.
- `SearchService` không còn chứa điều kiện mẫu như `pham vi dieu chinh`, `luat dau thau`; search core chỉ orchestration embedding/Qdrant/keyword candidates/dedup/response.
- Các rule boost/penalty được gom thành dataclass config riêng: phrase boost, prefix boost, missing phrase penalty và keyword phrase candidates.
- Thêm unit test `apps/api/app/services/tests/test_search_rerank_service.py` cho normalize tiếng Việt, keyword phrase, prefix boost, config disable rule và weak-match detection.

Kiểm tra đã chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/services/search_service.py apps/api/app/services/search_rerank_service.py apps/api/app/services/tests/test_search_rerank_service.py
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m unittest apps.api.app.services.tests.test_search_rerank_service
docker compose exec -T api python -m app.scripts.smoke_api_workflows
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Đã chuyển con trỏ hiện tại sang `Phase 3 / Mục tiêu 2`.

### Mục Tiêu 2 - Search Benchmark Fixtures

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu:
- Tạo benchmark fixtures cho truy vấn vật tư, phụ lục, điều khoản, ngày ban hành và đơn vị ban hành.

Phạm vi:
- Tạo dữ liệu fixture tối thiểu.
- Thêm command chạy benchmark local.
- Report top-k và metadata/citation liên quan.

Tiêu chí chấp nhận:
- Benchmark có thể chạy lại và so sánh thay đổi ranking.
- Có output rõ query nào pass/fail.

Kết quả:
- Thêm script `python -m app.scripts.benchmark_search_fixtures`.
- Script seed fixture tối thiểu cho truy vấn vật tư, phụ lục, điều khoản, ngày ban hành và đơn vị ban hành.
- Script index Qdrant bằng `EmbeddingService`/`QdrantService`, chạy `SearchService`, báo pass/fail theo expected chunk trong top-k và cleanup mặc định.
- Report top-k có metadata/citation gồm title, số văn bản, ngày ban hành, đơn vị ban hành, trang, `section_role` và `section_path`.
- Search API response và dashboard result có thêm `issuing_agency` để citation rõ hơn.

Kiểm tra đã chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/services/search_service.py apps/api/app/schemas/search.py apps/api/app/scripts/benchmark_search_fixtures.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api python -m app.scripts.benchmark_search_fixtures
docker compose run --rm --no-deps web npm run build
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Đã chuyển con trỏ hiện tại sang `Phase 3 / Mục tiêu 3`.

### Mục Tiêu 3 - Đánh Giá Embedding/Rerank Local

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu:
- Đánh giá embedding local và rerank local nếu benchmark cho thấy cần.

Phạm vi:
- Không dùng cloud.
- Ưu tiên cấu hình hiện có trước khi thêm dependency nặng.
- Ghi rõ tradeoff resource nếu đổi model local.

Tiêu chí chấp nhận:
- Có kết luận dựa trên benchmark, không đổi model theo cảm tính.

Kết quả:
- Mở rộng script `python -m app.scripts.benchmark_search_fixtures` để report cấu hình embedding, `hit_rate`, `mrr`, `mean_rank`, `top1` và khuyến nghị đánh giá.
- Thêm unit test `apps/api/app/services/tests/test_search_benchmark_evaluation.py` cho metric/evaluation.
- Benchmark chạy với `.env` local hiện tại: `EMBEDDING_BACKEND=sentence_transformers`, model `/models/embeddings/bkai-vietnamese-bi-encoder`, `EMBEDDING_DIMENSIONS=768`, CPU, `ALLOW_FAKE_EMBEDDINGS=false`.
- Kết quả benchmark: `5/5` pass, `hit_rate=1.00`, `mrr=1.00`, `mean_rank=1.0`, `top1=5/5`.
- Kết luận: giữ embedding/rerank hiện tại cho MVP; chưa đổi model local hoặc thêm reranker nặng vì benchmark chưa tạo bằng chứng cần đổi.
- Tradeoff nếu đổi model sau này: phải dùng Qdrant collection version mới hoặc reindex toàn bộ chunk khi backend/model/dimension thay đổi.

Kiểm tra đã chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/scripts/benchmark_search_fixtures.py apps/api/app/services/tests/test_search_benchmark_evaluation.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api python -m unittest app.services.tests.test_search_benchmark_evaluation
docker compose exec -T api python -m app.scripts.benchmark_search_fixtures
```

Ghi chú kiểm tra:
- `PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m unittest apps.api.app.services.tests.test_search_benchmark_evaluation` trên host không chạy được vì host thiếu dependency backend `pydantic_settings`; test đã pass trong container API.

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Đã chuyển con trỏ hiện tại sang `Phase 3 / Mục tiêu 4`.

### Mục Tiêu 4 - RAG Answer Endpoint Design

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu:
- Thiết kế nền tảng RAG local-only có citation.

Phạm vi:
- Thiết kế endpoint trả answer kèm chunk/document/source page citation.
- Không thay thế search MVP.
- Chỉ implement nếu retrieval benchmark đủ ổn.

Tiêu chí chấp nhận:
- RAG nếu bắt đầu phải trả lời kèm citation.
- Có fallback khi không đủ căn cứ trả lời.

Kết quả:
- Thêm schema `RagAnswerRequest`, `RagCitation`, `RagAnswerResponse` trong `apps/api/app/schemas/search.py`.
- Thêm `RagAnswerService` để tách RAG answer khỏi `SearchService`; search core vẫn chỉ phụ trách retrieval/ranking.
- Thêm endpoint `POST /api/v1/search/answer` trong search router, dùng auth hiện có và nhận cùng filter với semantic search.
- Endpoint local-only, không gọi cloud/LLM; MVP hiện tạo answer extractive từ chunk truy xuất.
- Citation trả về đủ `document_id`, `chunk_id`, `quote`, title, số văn bản, ngày ban hành, đơn vị ban hành, trang nguồn, `section_role` và `section_path`.
- Khi không đủ evidence theo score/overlap, endpoint trả `grounded=false`, `fallback_reason=insufficient_evidence` và không bịa câu trả lời.
- Thêm unit test `apps/api/app/services/tests/test_rag_answer_service.py`.
- Thêm smoke HTTP `python -m app.scripts.smoke_rag_answer`, seed benchmark fixture, gọi endpoint thật, kiểm tra citation và fallback, cleanup mặc định.

Kiểm tra đã chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/search.py apps/api/app/services/rag_answer_service.py apps/api/app/routers/search.py apps/api/app/services/tests/test_rag_answer_service.py apps/api/app/scripts/smoke_rag_answer.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api python -m unittest app.services.tests.test_rag_answer_service
docker compose exec -T api python -m app.scripts.smoke_rag_answer
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Phase 3 đã đạt điều kiện hoàn thành, đã đánh dấu Phase 3 `hoàn thành` và mở khóa Phase 4.

Điều kiện hoàn thành Phase 3:
- Có bộ benchmark search lặp lại được.
- Search result giải thích được bằng metadata/chunk citation.
- RAG nếu bắt đầu phải có citation và không phá search MVP.
- Đã đọc lại `ROADMAP.md` trước khi mở Phase 4.

## Phase 4 - Domain Modules

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu phase: mở rộng từ kho văn bản chung sang các module nghiệp vụ thực tế của phòng vật tư.

### Mục Tiêu 1 - Chọn Module Đầu Tiên

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu:
- Chọn module nghiệp vụ có giá trị cao nhất để làm trước.

Ứng viên:
- Hợp đồng và phụ lục hợp đồng.
- Công văn đến/đi.
- Quyết định, thông báo, đề nghị mua sắm.
- Phiếu/đề xuất vật tư nếu cần quản lý inventory workflow.

Tiêu chí chấp nhận:
- Có lý do chọn module đầu tiên.
- Scope MVP của module rõ ràng, không mở rộng quá mức.

Kết quả:
- Chọn module đầu tiên: **Hợp đồng và phụ lục hợp đồng**.
- Lý do chính: phù hợp nghiệp vụ phòng vật tư, tận dụng upload nhiều file/document core/OCR/chunking/search/RAG hiện có, đã có `business_type=contract`, benchmark có fixture hợp đồng/phụ lục, scope MVP rõ hơn phiếu vật tư/inventory.
- Ghi quyết định tại `docs/DOMAIN_MODULE_DECISION.md`.
- Scope MVP chỉ quản lý metadata hợp đồng liên kết document core, gồm số hợp đồng, tên hợp đồng, nhà cung cấp, ngày ký, hiệu lực, giá trị, tiền tệ, trạng thái và ghi chú.
- Không làm trong MVP: inventory, yêu cầu mua sắm, thanh toán/nghiệm thu nhiều bước, bảng dòng hàng vật tư chi tiết hoặc auto extraction bằng LLM.
- Boundary giữ đúng:
  - Backend: `router -> service -> repository`.
  - Frontend: `page -> composable -> service -> API`.
  - Search/RAG tiếp tục citation về document/chunk/page nguồn.

Kiểm tra đã chạy:

```bash
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Đã chuyển con trỏ hiện tại sang `Phase 4 / Mục tiêu 2`.

### Mục Tiêu 2 - Metadata Và Database Module

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu:
- Định nghĩa metadata riêng nhưng vẫn liên kết document core.

Phạm vi:
- Migration có UUID primary key.
- Mọi bảng nghiệp vụ có `created_at`, `updated_at`, `deleted_at`.
- Không hard delete dữ liệu nghiệp vụ.

Tiêu chí chấp nhận:
- Schema không phá document/search core.
- Metadata module có thể filter/search được.

Kết quả:
- Thêm model `ContractRecord` tại `apps/api/app/models/contract.py`.
- Import model vào `apps/api/app/db/base.py` và `apps/api/app/models/__init__.py`.
- Thêm quan hệ ORM 1-1 `Document.contract_record` và `ContractRecord.document`.
- Thêm migration `apps/api/alembic/versions/0011_contract_records.py`.
- Bảng `contract_records` có:
  - `id` UUID primary key.
  - `document_id` FK tới `documents.id`.
  - `contract_number`, `contract_title`, `supplier_name`.
  - `sign_date`, `effective_from`, `effective_to`.
  - `contract_value`, `currency`, `status`, `notes`.
  - `created_at`, `updated_at`, `deleted_at`.
- Dùng partial unique index `ux_contract_records_document_active` trên `document_id` với `deleted_at IS NULL`.
- Thêm index filter MVP: `contract_number`, `supplier_name`, `status`, `sign_date`, `effective_to`, đều kèm `deleted_at`.
- Cập nhật `docs/DOMAIN_MODULE_DECISION.md` với schema đã triển khai và hướng dẫn mục tiêu backend tiếp theo.

Kiểm tra đã chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/contract.py apps/api/app/models/document.py apps/api/app/models/__init__.py apps/api/app/db/base.py apps/api/alembic/versions/0011_contract_records.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api alembic upgrade head
docker compose exec -T api alembic current
docker compose exec -T api python - <<'PY'
from sqlalchemy.orm import configure_mappers
from app.models.contract import ContractRecord
from app.models.document import Document
configure_mappers()
print(Document.contract_record.property.uselist)
print(ContractRecord.document.property.uselist)
PY
docker compose exec -T postgres psql -U legal -d legal_doc_ai -c "select column_name, data_type, is_nullable from information_schema.columns where table_name = 'contract_records' order by ordinal_position;"
docker compose exec -T postgres psql -U legal -d legal_doc_ai -c "select indexname from pg_indexes where tablename = 'contract_records' order by indexname;"
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Đã chuyển con trỏ hiện tại sang `Phase 4 / Mục tiêu 3`.

### Mục Tiêu 3 - Backend Module API

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu:
- Thêm backend theo `router -> service -> repository`.

Phạm vi:
- CRUD/filter tối thiểu cho module đầu tiên.
- Permission theo RBAC hiện có.
- Audit log cho thao tác nghiệp vụ quan trọng.

Tiêu chí chấp nhận:
- API module hoạt động độc lập với upload/OCR core nhưng liên kết document được.

Kết quả:
- Thêm `apps/api/app/schemas/contract.py`.
- Thêm `apps/api/app/repositories/contract_repository.py`.
- Thêm `apps/api/app/services/contract_service.py`.
- Thêm `apps/api/app/routers/contracts.py` và include router trong `apps/api/app/main.py`.
- API endpoints:
  - `GET /api/v1/contracts`.
  - `GET /api/v1/contracts/{contract_id}`.
  - `POST /api/v1/contracts`.
  - `PATCH /api/v1/contracts/{contract_id}`.
  - `DELETE /api/v1/contracts/{contract_id}`.
- List/filter hỗ trợ query, document id, số hợp đồng, nhà cung cấp, trạng thái, ngày ký, hiệu lực, sort và pagination.
- Create/update validate document còn active, chặn trùng contract metadata active theo document, normalize currency và giữ metadata riêng trong `contract_records`.
- User đăng nhập được list/get/create/update; soft delete yêu cầu admin.
- Service ghi audit log `contract.created`, `contract.updated`, `contract.deleted`.
- Thêm smoke HTTP `python -m app.scripts.smoke_contract_api`.

Kiểm tra đã chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/contract.py apps/api/app/repositories/contract_repository.py apps/api/app/services/contract_service.py apps/api/app/routers/contracts.py apps/api/app/scripts/smoke_contract_api.py apps/api/app/main.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api python -m app.scripts.smoke_contract_api
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Đã chuyển con trỏ hiện tại sang `Phase 4 / Mục tiêu 4`.

### Mục Tiêu 4 - Frontend Module UI

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu:
- Thêm frontend theo `page -> composable -> service -> API`.

Phạm vi:
- Page list/filter/detail hoặc form tùy module.
- Tái sử dụng component list/filter/detail nếu có thể.
- Không tạo landing page.

Tiêu chí chấp nhận:
- UI có workflow nghiệp vụ rõ.
- Không gọi API trực tiếp trong component.

Kết quả:
- Thêm `apps/web/types/contract.ts`.
- Thêm `apps/web/services/contract.service.ts`.
- Thêm `apps/web/composables/useContracts.ts`.
- Thêm page `apps/web/pages/contracts.vue`.
- Thêm navigation `Contracts` trong `apps/web/app.vue`.
- Page `/contracts` có list/filter/pagination, form tạo/sửa metadata hợp đồng, link về document nguồn và action xóa mềm chỉ hiện cho admin.
- Frontend giữ đúng luồng `page -> composable -> service -> API`; component không gọi API trực tiếp.

Kiểm tra đã chạy:

```bash
docker compose run --rm --no-deps web npm run build
docker compose up -d web
curl -fsS http://localhost:3000/contracts
docker compose exec -T api python -m app.scripts.smoke_contract_api
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Phase 4 đã đạt điều kiện hoàn thành, đã đánh dấu Phase 4 `hoàn thành` và mở khóa Phase 5.

Điều kiện hoàn thành Phase 4:
- Module mới không phá upload/OCR/search core.
- Metadata module có thể filter/search được.
- UI giữ tái sử dụng component và service/composable hiện có.
- Đã đọc lại `ROADMAP.md` trước khi mở Phase 5.

## Phase 5 - Admin Configuration Và Governance

Trạng thái: đang làm.

Mục tiêu phase: để admin cấu hình hệ thống thay vì sửa code cho danh mục và rule cơ bản.

### Mục Tiêu 1 - Thiết Kế Danh Mục Admin

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu:
- Xác định danh mục cần quản lý: đơn vị/phòng ban, loại nghiệp vụ, loại văn bản.

Tiêu chí chấp nhận:
- Danh mục tối thiểu rõ ràng.
- Không biến admin config thành framework phức tạp.

Kết quả:
- Thêm `docs/ADMIN_CATEGORY_DESIGN.md`.
- Chốt danh mục MVP gồm:
  - Đơn vị/phòng ban.
  - Loại nghiệp vụ.
  - Loại văn bản.
- Giữ `departments` là bảng/entity riêng vì đã liên kết `users.department_id` và `documents.department_id`.
- Đề xuất dùng `admin_catalog_items` giới hạn cho `business_type` và `document_type`, không tạo framework config chung.
- Ghi rõ seed MVP, API boundary, frontend boundary, fallback khi catalog API lỗi và tiêu chí cho mục tiêu CRUD tiếp theo.

Kiểm tra đã chạy:

```bash
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Đã chuyển con trỏ hiện tại sang `Phase 5 / Mục tiêu 2`.

### Mục Tiêu 2 - CRUD Danh Mục Có Audit

Trạng thái: hoàn thành ngày 2026-06-06.

Mục tiêu:
- Admin thay đổi danh mục có audit log.

Phạm vi:
- Backend CRUD theo kiến trúc chuẩn.
- Soft delete cho dữ liệu nghiệp vụ.
- Permission admin-only.

Tiêu chí chấp nhận:
- Audit log ghi được create/update/delete.

Kết quả:
- Thêm migration `apps/api/alembic/versions/0012_admin_catalogs.py`.
- Thêm model `AdminCatalogItem` và mở rộng model `Department` với `description`, `sort_order`, `is_active`.
- Thêm `apps/api/app/schemas/catalog.py`.
- Thêm `apps/api/app/repositories/catalog_repository.py`.
- Thêm `apps/api/app/services/catalog_service.py`.
- Thêm `apps/api/app/routers/catalogs.py` và include router trong `apps/api/app/main.py`.
- API read option cho user đăng nhập:
  - `GET /api/v1/catalogs/departments`.
  - `GET /api/v1/catalogs/business-types`.
  - `GET /api/v1/catalogs/document-types`.
- API CRUD admin-only:
  - `POST/PATCH/DELETE /api/v1/admin/catalogs/departments`.
  - `GET/POST/PATCH/DELETE /api/v1/admin/catalogs/items`.
- Thêm smoke HTTP `python -m app.scripts.smoke_catalog_api`.

Kiểm tra đã chạy:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/models/catalog.py apps/api/app/models/department.py apps/api/app/db/base.py apps/api/app/models/__init__.py apps/api/app/schemas/catalog.py apps/api/app/repositories/catalog_repository.py apps/api/app/services/catalog_service.py apps/api/app/routers/catalogs.py apps/api/app/scripts/smoke_catalog_api.py apps/api/app/main.py apps/api/alembic/versions/0012_admin_catalogs.py
docker compose up -d api postgres redis qdrant
docker compose exec -T api alembic upgrade head
docker compose restart api
docker compose exec -T api alembic current
docker compose exec -T api python -m app.scripts.smoke_catalog_api
docker compose exec -T api python -m app.scripts.smoke_contract_api
git diff --check
```

Sau khi hoàn thành:
- Đã đọc lại `ROADMAP.md`.
- Đã cập nhật `PROJECT_STATUS.md` với kết quả và kiểm tra đã chạy.
- Đã cập nhật mục tiêu này thành `hoàn thành`.
- Đã chuyển con trỏ hiện tại sang `Phase 5 / Mục tiêu 3`.

### Mục Tiêu 3 - Frontend Dùng Option Từ API

Trạng thái: chưa làm.

Mục tiêu:
- Các form phù hợp lấy option từ API thay vì hardcode.

Tiêu chí chấp nhận:
- UI vẫn có fallback hợp lý khi API lỗi.
- Không phá upload/document metadata hiện có.

### Mục Tiêu 4 - Trang Status Tối Thiểu

Trạng thái: khóa.

Mục tiêu:
- Thêm status cho OCR/model/Qdrant.

Tiêu chí chấp nhận:
- Admin xem được trạng thái cơ bản.
- Không thêm observability phức tạp quá MVP.

Điều kiện hoàn thành Phase 5:
- Admin thay đổi danh mục có audit log.
- Frontend lấy option từ API cho các field phù hợp.
- Có trạng thái model/OCR/Qdrant tối thiểu.
- Đã đọc lại `ROADMAP.md` trước khi mở Phase 6.

## Phase 6 - On-Prem Production Hardening

Trạng thái: khóa đến khi Phase 5 hoàn thành.

Mục tiêu phase: chuẩn bị vận hành nội bộ on-prem một cách có kiểm soát.

### Mục Tiêu 1 - Chuẩn Hóa Env Và Secret

Trạng thái: khóa.

Mục tiêu:
- Chuẩn hóa `.env`, secret, CORS và default admin password policy.

Tiêu chí chấp nhận:
- Cài đặt production nội bộ không dùng default secret/admin password.

### Mục Tiêu 2 - Storage Volumes Và Backup/Restore

Trạng thái: khóa.

Mục tiêu:
- Tài liệu storage volumes cho PostgreSQL, Qdrant và uploads.
- Viết backup/restore runbook.

Tiêu chí chấp nhận:
- Có runbook backup/restore có thể làm theo.

### Mục Tiêu 3 - Health, Readiness Và Logs

Trạng thái: khóa.

Mục tiêu:
- Health/readiness phân biệt service sống với service sẵn sàng xử lý workflow.
- Kiểm tra log policy tối thiểu.

Tiêu chí chấp nhận:
- Health check hữu ích cho api, worker và data services liên quan.

### Mục Tiêu 4 - Compose Resource Limits Và Upload Policy

Trạng thái: khóa.

Mục tiêu:
- Kiểm tra resource limits Docker Compose, storage volumes và file upload limits.

Tiêu chí chấp nhận:
- Có cấu hình hoặc tài liệu rõ cho giới hạn vận hành nội bộ.

Điều kiện hoàn thành Phase 6:
- Có runbook cài đặt, nâng cấp, backup, restore và troubleshoot.
- Cấu hình production nội bộ không dùng default secret/admin password.
- Observability tối thiểu đủ cho vận hành on-prem.
