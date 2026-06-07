# Kế Hoạch Task Tiếp Theo

Cập nhật lần cuối: 2026-06-07

Tài liệu này là **checklist thực thi của phase đang làm**, bám theo `ROADMAP.md`. Khi người dùng nói `thực hiện TASK_NEXT.md`, agent phải bắt đầu từ mục đầu tiên có trạng thái `chưa làm` hoặc `đang làm`.

Lịch sử phase đã hoàn thành, kết quả khảo sát và log kiểm tra nằm trong `PROJECT_STATUS.md` và `ROADMAP.md` (không lưu lại trong file này).

## Quy Tắc Thực Thi Bắt Buộc

- Trước khi bắt đầu bất kỳ mục tiêu nào: đọc lại `ROADMAP.md`, `PROJECT_STATUS.md` và `TASK_NEXT.md`.
- Chỉ làm một mục tiêu nhỏ tại một thời điểm.
- Xong mục tiêu nào phải kiểm tra tiêu chí chấp nhận, cập nhật `PROJECT_STATUS.md` và `TASK_NEXT.md` (trạng thái mục tiêu, kết quả khảo sát nếu có).
- **Auto commit:** sau khi mục tiêu pass tiêu chí chấp nhận và kiểm tra bắt buộc đã chạy (hoặc lý do chưa chạy được đã ghi rõ), bắt buộc commit bằng skill `project-git-manager`; không chờ user yêu cầu riêng.
- Sau khi xong từng mục tiêu: đọc lại `ROADMAP.md` để xác nhận ưu tiên còn đúng.
- Sau khi xong một phase: đọc lại `ROADMAP.md`, ghi nhận phase hoàn thành trong `PROJECT_STATUS.md`, **thay nội dung `TASK_NEXT.md` bằng checklist phase kế tiếp**, commit, rồi mới mở khóa phase sau.
- Giữ đúng stack cố định và kiến trúc:
  - Backend: `router -> service -> repository`.
  - Frontend: `page -> composable -> service -> API`.
- Trước mỗi mục tiêu: đọc skill kỹ thuật ghi trong mục tiêu (nếu có) và `AGENTS.md`.

## Con Trỏ Hiện Tại

Phase trước: Phase 13 hoàn thành ngày 2026-06-07.

Phase hiện tại: Phase 14 - Gợi Ý Metadata Module Và Onboarding Sau OCR.

Mục tiêu tiếp theo: Phase 14 / Mục Tiêu 6 - Smoke Onboarding Và Hoàn Tất Phase 14.

Điều kiện chuyển sang mục tiêu kế tiếp:
- Mục tiêu hiện tại pass tiêu chí chấp nhận.
- Kiểm tra bắt buộc đã chạy hoặc lý do chưa chạy được đã ghi trong `PROJECT_STATUS.md`.
- `ROADMAP.md` đã được đọc lại sau khi hoàn thành mục tiêu.
- Đã auto commit thay đổi liên quan.

---

## Phase 14 - Gợi Ý Metadata Module Và Onboarding Sau OCR

Trạng thái: đang làm (bắt đầu 2026-06-07; mục tiêu 1–4 hoàn thành).

Mục tiêu phase: nối classifier OCR rule-based (`DocumentClassifierService`) với 4 module nghiệp vụ — gợi ý `business_type`, loại module và pre-fill form; không tự tạo bản ghi module mà không có xác nhận người dùng.

Điều kiện hoàn thành phase:
- Có quyết định mapping trong `docs/DOMAIN_MODULE_DECISION.md`.
- API `onboarding-suggestions` + UI document detail/list + smoke tái chạy được.
- Ít nhất một luồng mỗi module: OCR searchable → gợi ý → áp dụng business_type / mở form tạo metadata pre-fill.

Không làm trong phase này:
- Không LLM / model inference mới.
- Không auto-create module record im lặng.
- Không `document_relations`, inventory, workflow phê duyệt nhiều bước.
- Không re-index Qdrant hàng loạt.

### Mục Tiêu 1 - Thiết Kế Mapping Classifier → business_type/Module

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `solution-architect`, `vn-admin-doc-ocr-classifier`, `project-git-manager`.

Mục tiêu:
- Chốt bảng mapping `document_type` → `business_type` catalog + module target và map field classifier → form module.

Phạm vi:
- Cập nhật `docs/DOMAIN_MODULE_DECISION.md` mục module onboarding (mới).
- Tham chiếu `DocumentClassifierService`, catalog `business_type` migration `0012`, pre-fill form hiện có trên `/contracts`, `/dispatches`, `/decisions`, `/procurements`.
- Không code trong mục tiêu này.

Tiêu chí chấp nhận:
- Có spec đủ rõ để implement service/API/UI mục tiêu 2–5.
- Ghi rõ ngưỡng confidence, guard manual review, heuristic `CV` incoming/outgoing.

Kiểm tra bắt buộc:

```bash
git diff --check
```

### Mục Tiêu 2 - ModuleOnboardingService Và API onboarding-suggestions

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- Service gợi ý `business_type` + module pre-fill; endpoint read-only `GET /api/v1/documents/{document_id}/onboarding-suggestions`.

Phạm vi:
- `ModuleOnboardingService` (hoặc mở rộng classifier service): `suggest_business_type()`, `suggest_module_record()`.
- Schema response: `target_module`, `suggested_business_type`, `suggested_fields`, `confidence`, `reasons`.
- Router documents; không thay đổi CRUD module hiện có.

Tiêu chí chấp nhận:
- API trả gợi ý hợp lệ cho document searchable chưa có module active (fixture thủ công hoặc unit test).
- Không gợi ý khi document đã có bản ghi module tương ứng.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.check_document_classifier
git diff --check
```

### Mục Tiêu 3 - Worker/Audit Gợi Ý business_type Có Kiểm Soát

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `ocr-pipeline`, `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- Worker hoặc audit ghi nhận gợi ý `business_type` khi upload chưa chọn loại; không ghi đè metadata manual review.

Phạm vi:
- Chỉ apply/auto-suggest khi `business_type` rỗng hoặc chưa do user chọn; respect `metadata_reviewed_at` / `metadata_source`.
- Audit `document.onboarding_suggested` hoặc tương đương (metadata JSON gọn).
- Có thể gộp vào mục tiêu 2 nếu API đủ; ghi rõ trong `PROJECT_STATUS.md` nếu bỏ qua.

Tiêu chí chấp nhận:
- Upload không chọn business_type → sau OCR có audit/gợi ý; upload đã chọn → không đổi business_type.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_api_workflows
git diff --check
```

### Mục Tiêu 4 - Document Detail: Banner Gợi Ý Và CTA Tạo Metadata

Trạng thái: hoàn thành (2026-06-07).

Skill bắt buộc: `frontend-nuxt`, `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- Card/banner **Gợi ý metadata** trên `/documents/[id]`; nút áp dụng business_type và tạo metadata module pre-fill.

Phạm vi:
- Composable/service gọi `onboarding-suggestions`; reuse form module hiện có (deep link `create=1` hoặc inline CTA).
- Low-confidence: nhắc review metadata document, không chặn workflow.

Tiêu chí chấp nhận:
- User thấy gợi ý và mở form module pre-fill trong ≤2 thao tác cho ≥1 fixture manual/smoke.

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 5 - Document List: Badge/Filter Thiếu Metadata Module

Trạng thái: chưa làm (tiếp theo).

Skill bắt buộc: `frontend-nuxt`, `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- List documents hiển thị badge “chưa có metadata module”; filter `missing_module_metadata=true`.

Phạm vi:
- Mở rộng API list documents (query param + response flag) nếu cần; UI list/index hoặc trang documents hiện có.
- Không pagination regression.

Tiêu chí chấp nhận:
- Filter trả đúng document có `business_type` module nhưng thiếu bản ghi active.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_api_workflows
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 6 - Smoke Onboarding Và Hoàn Tất Phase 14

Trạng thái: chưa làm.

Skill bắt buộc: `semantic-search-rag`, `ocr-pipeline`, `project-git-manager`.

Mục tiêu:
- Script `smoke_module_onboarding.py`; regression toàn phase; đóng Phase 14.

Phạm vi:
- Seed ≥1 fixture mỗi module (`contract`, `dispatch`, `decision`, `procurement`): classify → suggestion → apply → tạo metadata.
- Cập nhật `ROADMAP.md`, `PROJECT_STATUS.md`; thay `TASK_NEXT.md` bằng phase kế tiếp hoặc ghi “chưa lập phase 15”.

Tiêu chí chấp nhận:
- Phase 14 đạt tiêu chí hoàn thành trong `ROADMAP.md`.
- Auto commit sau khi pass kiểm tra.

Kiểm tra bắt buộc:

```bash
docker compose exec -T api python -m app.scripts.smoke_module_onboarding
docker compose exec -T api python -m app.scripts.smoke_api_workflows
docker compose exec -T api python -m app.scripts.smoke_procurement_api
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.check_document_classifier
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```
