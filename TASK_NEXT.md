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

Phase trước: Phase 16 hoàn thành ngày 2026-06-07.

Phase hiện tại: Phase 17 - RAG Generative Local LLM (Ollama On-Prem).

Mục tiêu tiếp theo: Phase 17 / Mục Tiêu 1 - Thiết Kế Generative RAG, Prompt Và Env Contract.

Điều kiện chuyển sang mục tiêu kế tiếp:
- Mục tiêu hiện tại pass tiêu chí chấp nhận.
- Kiểm tra bắt buộc đã chạy hoặc lý do chưa chạy được đã ghi trong `PROJECT_STATUS.md`.
- `ROADMAP.md` đã được đọc lại sau khi hoàn thành mục tiêu.
- Đã auto commit thay đổi liên quan.

---

## Phase 17 - RAG Generative Local LLM (Ollama On-Prem)

Trạng thái: đang làm (bắt đầu 2026-06-07).

Mục tiêu phase: nâng `POST /api/v1/search/answer` sang generative local-only qua Ollama, citation bắt buộc, fallback extractive khi LLM không sẵn sàng.

Điều kiện hoàn thành phase:
- Quyết định generation + prompt + validation ghi trong `docs/DOMAIN_MODULE_DECISION.md`.
- `RAG_GENERATION_BACKEND=extractive` (default): regression `smoke_rag_answer` pass không cần Ollama.
- `RAG_GENERATION_BACKEND=ollama` + profile `llm`: smoke generative pass (`generation_mode=generative`, ≥1 citation hợp lệ).
- Ollama down/timeout: fallback extractive, không 500.
- Runbook dev + deploy (RAM/GPU sizing) trong repo; frontend build + regression Phase 16 pass.

Không làm trong phase này:
- Cloud LLM / OpenAI API.
- Fine-tune, RAG agent multi-step, tool calling, streaming SSE.
- Thay embedding, re-index Qdrant, đổi chunking.
- LLM trong worker OCR.
- vLLM production path (chỉ ghi chú future trong tài liệu).

Sizing tham chiếu (`ROADMAP.md`):
- **core** (mặc định): ~8 GB RAM host — không chạy Ollama.
- **llm-dev**: +6 GB limit Ollama, model `qwen2.5:3b-instruct` — host ≥16 GB.
- **llm-prod-cpu**: +10 GB, model 7B — host ≥32 GB.
- **llm-prod-gpu**: host 16 GB RAM + ≥8 GB VRAM.

### Mục Tiêu 1 - Thiết Kế Generative RAG, Prompt Và Env Contract

Trạng thái: chưa làm (tiếp theo).

Skill bắt buộc: `solution-architect`, `semantic-search-rag`.

Mục tiêu:
- Chốt luồng generative, prompt MVP, citation validation và hợp đồng env trước khi code.

Phạm vi:
- Đọc `RagAnswerService`, schema `RagAnswerResponse`/`RagCitation`, `ROADMAP.md` Phase 17 (Ollama, profile `llm`, sizing).
- Ghi mục mới **RAG Generative (Phase 17)** trong `docs/DOMAIN_MODULE_DECISION.md`: backend `extractive|ollama`, luồng retrieval → context → LLM → validator → fallback; prompt system/user; map `[1]..[n]` → `citations[]`; `fallback_reason` (`llm_unavailable`, `validation_failed`, `insufficient_evidence`).
- Liệt kê biến env: `RAG_GENERATION_BACKEND`, `OLLAMA_BASE_URL`, `RAG_LLM_MODEL`, `RAG_LLM_TIMEOUT_SECONDS`, `RAG_LLM_MAX_CONTEXT_CHARS`, `RAG_LLM_MAX_OUTPUT_TOKENS`, `RAG_LLM_TEMPERATURE`, limit Compose Ollama.
- Ghi khảo sát trong `PROJECT_STATUS.md`.
- Không code backend/frontend/compose trong mục tiêu này.

Tiêu chí chấp nhận:
- Tài liệu đủ rõ để implement mục tiêu 2–4.
- Ghi rõ: default `extractive`; `/health/ready` không fail khi Ollama down; worker không gọi LLM.

Kiểm tra bắt buộc:

```bash
git diff --check
```

### Mục Tiêu 2 - LocalLLMService Và Settings

Trạng thái: chưa làm.

Skill bắt buộc: `backend-fastapi`, `semantic-search-rag`.

Mục tiêu:
- Client Ollama HTTP (health + chat), settings mirror pattern `embedding_backend`.

Phạm vi:
- Settings trong `config.py`: `rag_generation_backend`, `ollama_base_url`, `rag_llm_model`, timeout, max context/output tokens, temperature.
- `LocalLLMService`: `is_available()`, `generate(prompt, system)` — gọi Ollama `/api/chat` hoặc `/api/generate`; timeout; exception có cấu trúc (không leak stack ra router).
- Unit test mock HTTP: available/unavailable/timeout.

Tiêu chí chấp nhận:
- `RAG_GENERATION_BACKEND=extractive` không gọi Ollama.
- Service tách khỏi router; không side-effect DB.

Kiểm tra bắt buộc:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/services/local_llm_service.py \
  apps/api/app/core/config.py
docker compose exec -T api python -m unittest app.services.tests.test_local_llm_service -v
git diff --check
```

### Mục Tiêu 3 - Docker Compose Profile `llm` Và Ollama Service

Trạng thái: chưa làm.

Skill bắt buộc: `solution-architect`, `project-git-manager`.

Mục tiêu:
- Service `ollama` optional qua profile `llm`; dev chạy core không cần LLM.

Phạm vi:
- `docker-compose.yml`: service `ollama` (`ollama/ollama`), `profiles: [llm]`, volume `ollama_data`, healthcheck, limits `OLLAMA_CPU_LIMIT` / `OLLAMA_MEMORY_LIMIT`.
- `api` nhận env Ollama; **không** hard-depend Ollama khi profile tắt (readiness api vẫn pass).
- File tùy chọn `docker-compose.llm-gpu.yml` (NVIDIA reservation) — comment hướng dẫn.
- Cập nhật `.env.example` (hoặc ghi trong runbook mục tiêu 7 nếu chưa có `.env.example`).
- Cập nhật bảng resource trong `docs/COMPOSE_RESOURCE_UPLOAD_RUNBOOK.md` (dòng ollama).

Tiêu chí chấp nhận:
- `docker compose config` pass (không profile).
- `docker compose --profile llm config` render service ollama + volume.
- `docker compose up -d` không kéo ollama; `--profile llm up -d` start ollama.

Kiểm tra bắt buộc:

```bash
docker compose config
docker compose --profile llm config
git diff --check
```

### Mục Tiêu 4 - RagAnswerService Generative, Context Builder Và Fallback

Trạng thái: chưa làm.

Skill bắt buộc: `backend-fastapi`, `semantic-search-rag`.

Mục tiêu:
- Nhánh generative sau retrieval; fallback extractive khi fail.

Phạm vi:
- `RagContextBuilder`: format top-k chunk (index, chunk_id, metadata, snippet) cho prompt tiếng Việt.
- `CitationValidator`: marker `[n]` / chunk_id phải thuộc retrieval set; quote overlap tối thiểu.
- Mở rộng `RagAnswerService.answer()`: nếu `rag_generation_backend=ollama` và LLM available → generative; else extractive hiện tại.
- Response thêm `generation_mode`, `model_name?`, `latency_ms?`; `fallback_reason` mở rộng (`llm_unavailable`, `validation_failed`).
- Giữ hành vi extractive **identical** khi backend=extractive.

Tiêu chí chấp nhận:
- Unit test: generative mock → `generation_mode=generative`; Ollama down → extractive + `llm_unavailable`.
- Không đổi Qdrant payload / SearchService contract.

Kiểm tra bắt buộc:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/services/rag_answer_service.py \
  apps/api/app/services/rag_context_builder.py
docker compose exec -T api python -m unittest app.services.tests.test_rag_answer_service -v
docker compose exec -T api python -m app.scripts.smoke_rag_answer
git diff --check
```

### Mục Tiêu 5 - API Schema, Router Và Ops LLM Status

Trạng thái: chưa làm.

Skill bắt buộc: `backend-fastapi`, `project-git-manager`.

Mục tiêu:
- Schema response mở rộng; admin thấy trạng thái LLM trên `/ops/system-status`.

Phạm vi:
- Schema Pydantic: `generation_mode`, `model_name`, `latency_ms`, `fallback_reason` mở rộng (backward compatible optional fields).
- Router `POST /search/answer` trả field mới; không breaking client cũ (field optional).
- `OpsService._get_llm_status()`: backend, model, reachable, model_loaded (nếu query được).
- Mở rộng `SystemStatusRead` + smoke health nếu cần.

Tiêu chí chấp nhận:
- Extractive smoke pass; system-status có component LLM (`ok`/`degraded`/`unavailable`).
- Ollama down: answer vẫn 200 extractive fallback.

Kiểm tra bắt buộc:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile \
  apps/api/app/schemas/search.py \
  apps/api/app/routers/search.py \
  apps/api/app/services/ops_service.py
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_health_checks
git diff --check
```

### Mục Tiêu 6 - Frontend Dashboard Và Trang Status

Trạng thái: chưa làm.

Skill bắt buộc: `frontend-nuxt`, `project-git-manager`.

Mục tiêu:
- UX phân biệt extractive/generative; loading và fallback rõ ràng.

Phạm vi:
- Types `RagAnswerResponse` mở rộng trong `search` types/service.
- Dashboard card **Hỏi đáp (RAG)**: badge **Extractive** / **Generative (local)**; message fallback (`llm_unavailable`, `validation_failed`); loading “Đang tổng hợp câu trả lời…”; disable nút Hỏi khi pending.
- `/status`: card LLM (backend, model, reachable) qua composable/service ops hiện có.
- Không gọi API trực tiếp trong component.

Tiêu chí chấp nhận:
- Extractive-only stack: badge Extractive; không lỗi UI.
- Build pass; semantic search regression trên dashboard không đổi.

Kiểm tra bắt buộc:

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```

### Mục Tiêu 7 - Runbook Dev/Deploy Và Env Documentation

Trạng thái: chưa làm.

Skill bắt buộc: `solution-architect`, `project-git-manager`.

Mục tiêu:
- Runbook vận hành Ollama on-prem; dev clone chạy được không LLM; prod có hướng dẫn sizing.

Phạm vi:
- `docs/RAG_LLM_RUNBOOK.md`: pull model, profile dev/prod, GPU override, troubleshoot OOM/timeout, fallback behavior, smoke commands.
- Cập nhật `docs/COMPOSE_RESOURCE_UPLOAD_RUNBOOK.md` (ollama limits, `ollama_data` backup pointer).
- Cập nhật `docs/RAG_ANSWER_RUNBOOK.md` (link generative + extractive paths).
- `.env.example` hoặc section README ngắn nếu project đã có pattern env mẫu.

Tiêu chí chấp nhận:
- Dev mới đọc runbook biết: default extractive; bật LLM bằng `--profile llm` + pull model.
- Prod checklist: firewall 11434 nội bộ, backup volume, RAM/GPU table.

Kiểm tra bắt buộc:

```bash
git diff --check
```

### Mục Tiêu 8 - Smoke Generative, Regression Và Hoàn Tất Phase

Trạng thái: chưa làm.

Skill bắt buộc: `backend-fastapi`, `frontend-nuxt`, `project-git-manager`.

Mục tiêu:
- Smoke generative tái chạy được; đóng Phase 17 trong tài liệu trạng thái.

Phạm vi:
- Script `python -m app.scripts.smoke_rag_generative`: yêu cầu profile `llm` + model pulled; seed fixture searchable → POST answer → assert `generation_mode=generative`, citations hợp lệ.
- Script hoặc flag test fallback: Ollama unreachable → extractive + `llm_unavailable` (có thể trong cùng smoke hoặc unit integration).
- Regression extractive (no profile): `smoke_rag_answer`, `smoke_relation_suggestions`.
- Cập nhật `docs/DOMAIN_MODULE_DECISION.md` (triển khai hoàn tất), `ROADMAP.md` Phase 17 hoàn thành, `PROJECT_STATUS.md`.
- Thay `TASK_NEXT.md` bằng placeholder Phase 18 hoặc “chưa lập” theo `ROADMAP.md`.

Tiêu chí chấp nhận:
- Tiêu chí hoàn thành Phase 17 trong `ROADMAP.md` đạt.
- Auto commit sau khi pass kiểm tra.

Kiểm tra bắt buộc:

```bash
# Extractive regression (default, không profile llm)
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_relation_suggestions

# Generative (profile llm, sau ollama pull qwen2.5:3b-instruct)
docker compose --profile llm exec -T api python -m app.scripts.smoke_rag_generative

WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
git diff --check
```
