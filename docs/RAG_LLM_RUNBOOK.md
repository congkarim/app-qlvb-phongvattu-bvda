# RAG Local LLM (Ollama) Runbook

Cập nhật lần cuối: 2026-06-07

Hướng dẫn vận hành **RAG generative local-only** qua **Ollama** on-prem. Mặc định hệ thống dùng **extractive** — không cần LLM để dev, smoke CI hoặc production chỉ trích dẫn chunk.

Thiết kế chi tiết: `docs/DOMAIN_MODULE_DECISION.md` (mục RAG Generative Phase 17). Sizing tổng thể: `ROADMAP.md` Phase 17.

## Tóm Tắt Nhanh

| Chế độ | `RAG_GENERATION_BACKEND` | Compose | Khi nào dùng |
| --- | --- | --- | --- |
| Extractive (mặc định) | `extractive` | `docker compose up -d` | Dev máy yếu, CI, prod không cần tổng hợp LLM |
| Generative local | `ollama` | `--profile llm` + pull model | Prod/dev máy đủ RAM/GPU, cần câu trả lời tổng hợp |

- `/health/ready` **không** phụ thuộc Ollama — API vẫn ready khi LLM down.
- Ollama down / timeout / validation fail → API **200** với extractive fallback và `fallback_reason` (`llm_unavailable`, `validation_failed`).
- Worker OCR **không** gọi LLM — tránh tranh RAM với model.

## Biến Môi Trường

Copy từ `.env.example`. Các biến chính:

```env
RAG_GENERATION_BACKEND=extractive          # hoặc ollama
OLLAMA_BASE_URL=http://ollama:11434        # prod tách host: http://llm-host:11434
RAG_LLM_MODEL=qwen2.5:3b-instruct          # prod khuyến nghị qwen2.5:7b-instruct
RAG_LLM_TIMEOUT_SECONDS=120                # dev CPU; prod GPU ~90
RAG_LLM_MAX_CONTEXT_CHARS=8000
RAG_LLM_MAX_OUTPUT_TOKENS=512
RAG_LLM_TEMPERATURE=0.1
OLLAMA_CPU_LIMIT=2
OLLAMA_MEMORY_LIMIT=6G
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
```

Sau khi sửa `.env`, recreate container `api`:

```bash
docker compose up -d api
```

## Dev — Không LLM (Mặc Định)

Clone repo, chạy stack core như bình thường:

```bash
cp .env.example .env
docker compose up -d
```

Giữ `RAG_GENERATION_BACKEND=extractive`. Service `ollama` **không** start.

Smoke extractive (bắt buộc regression):

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer
```

Máy **8 GB RAM** vẫn dev được OCR + search + RAG extractive.

## Dev — Bật LLM (`--profile llm`)

**Yêu cầu:** host khuyến nghị **≥16 GB RAM** (core ~8G + Ollama 6G limit + model 3B).

1. Cập nhật `.env`:

```env
RAG_GENERATION_BACKEND=ollama
RAG_LLM_MODEL=qwen2.5:3b-instruct
RAG_LLM_TIMEOUT_SECONDS=120
OLLAMA_MEMORY_LIMIT=6G
```

2. Start stack kèm profile:

```bash
docker compose --profile llm up -d
```

3. Pull model **một lần** (cần internet lần đầu):

```bash
docker compose exec ollama ollama pull qwen2.5:3b-instruct
docker compose exec ollama ollama list
```

4. Kiểm tra ops:

```bash
curl -s http://localhost:8000/api/v1/ops/system-status \
  -H "Authorization: Bearer $TOKEN" | jq .llm
```

Kỳ vọng: `status=ok`, `details.reachable=true`, `details.model_loaded=true`.

5. Smoke generative (sau khi Objective 8 có script):

```bash
docker compose --profile llm exec -T api python -m app.scripts.smoke_rag_generative
```

6. UI: `/dashboard` → card **Hỏi đáp (RAG)** — badge **Generative (local)** khi thành công; `/status` → card **LLM (RAG)**.

Latency CPU 3B: thường **15–45 s** — UI hiển thị “Đang tổng hợp câu trả lời…”.

## Dev GPU (Tùy Chọn)

Host cần **NVIDIA Container Toolkit**. Dùng override:

```bash
docker compose -f docker-compose.yml -f docker-compose.llm-gpu.yml --profile llm up -d
docker compose exec ollama ollama pull qwen2.5:3b-instruct
```

File: `docker-compose.llm-gpu.yml`. Không bắt buộc cho MVP.

## Production On-Prem

### Sizing khuyến nghị

| Profile | Model | RAM limit Ollama | CPU | GPU | RAM host tổng |
| --- | --- | --- | --- | --- | --- |
| Core extractive | — | — | — | — | **8 GB** tối thiểu |
| LLM dev / smoke | `qwen2.5:3b-instruct` | 6G | 2 | Không | **16 GB** |
| LLM prod CPU | `qwen2.5:7b-instruct` | 10G | 4 | Không | **32 GB** |
| LLM prod GPU | `qwen2.5:7b-instruct` | 4G | 2 | **≥8 GB VRAM** | **16 GB** host + GPU |

Volume `ollama_data`: ~**2 GB** (3B Q4), ~**5 GB** (7B Q4).

### Topology

| Quy mô | Gợi ý |
| --- | --- |
| Phòng ban nhỏ (≤10 user) | All-in-one: core + `ollama` trên một server 32 GB |
| OCR nhiều / peak cao | Tách LLM: `OLLAMA_BASE_URL=http://llm-host:11434` trên server GPU riêng |
| HA multi-instance Ollama | Ngoài scope MVP Phase 17 |

**Ví dụ prod CPU-only (32 GB):**

```env
APP_ENV=production
RAG_GENERATION_BACKEND=ollama
RAG_LLM_MODEL=qwen2.5:7b-instruct
RAG_LLM_TIMEOUT_SECONDS=90
RAG_LLM_MAX_CONTEXT_CHARS=12000
RAG_LLM_MAX_OUTPUT_TOKENS=768
OLLAMA_CPU_LIMIT=4
OLLAMA_MEMORY_LIMIT=10G
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
```

**Ví dụ prod GPU:**

```env
RAG_LLM_MODEL=qwen2.5:7b-instruct
OLLAMA_MEMORY_LIMIT=4G
OLLAMA_CPU_LIMIT=2
```

```bash
docker compose -f docker-compose.yml -f docker-compose.llm-gpu.yml --profile llm up -d
```

### Checklist go-live

- [ ] Pull/load model **offline** trước go-live (`ollama pull` trên máy có internet, hoặc restore volume `ollama_data`).
- [ ] `RAG_GENERATION_BACKEND=ollama` chỉ khi Ollama + model đã sẵn sàng.
- [ ] Firewall: port **11434 chỉ nội bộ** nếu LLM tách host — **không** expose public Internet.
- [ ] Backup volume `ollama_data` (xem `docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md`).
- [ ] Giám sát `/status`: `generation_backend`, `reachable`, `model_loaded`.
- [ ] Production guard: `JWT_SECRET_KEY`, `ADMIN_PASSWORD`, `CORS`, `DATABASE_URL` (xem `docs/ON_PREM_ENV_RUNBOOK.md`).
- [ ] Tránh chạy OCR job lớn và RAG generative đồng thời trên máy 16 GB — giữ `OLLAMA_NUM_PARALLEL=1`.

### Load model offline

Trên máy có internet:

```bash
docker compose --profile llm up -d ollama
docker compose exec ollama ollama pull qwen2.5:7b-instruct
```

Backup volume để mang sang site air-gap:

```bash
docker compose stop ollama
docker run --rm \
  -v app-qlvb-phongvattu_ollama_data:/data:ro \
  -v "$PWD/backups:/backups" \
  alpine tar czf /backups/ollama_$(date +%Y%m%d_%H%M%S).tgz -C /data .
docker compose --profile llm up -d ollama
```

Restore: xem `docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md`.

## Hành Vi Fallback

Luồng `POST /api/v1/search/answer`:

```text
retrieval → (nếu backend=ollama và Ollama healthy) → LLM generate → CitationValidator
         → fail bất kỳ bước → extractive fallback (Phase 12)
```

| `fallback_reason` | Ý nghĩa | HTTP | UI dashboard |
| --- | --- | --- | --- |
| `insufficient_evidence` | Không đủ chunk căn cứ | 200 | Cảnh báo vàng, không grounded |
| `llm_unavailable` | Ollama down / timeout / lỗi HTTP | 200 | Info + answer extractive nếu có căn cứ |
| `validation_failed` | LLM trả lời không pass validator citation | 200 | Cảnh báo + extractive fallback |

Response thêm: `generation_mode` (`extractive` \| `generative`), `model_name`, `latency_ms`.

## Smoke Và Kiểm Tra

### Extractive (default, không profile `llm`)

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_health_checks
```

Health smoke kiểm tra component `llm`: backend `extractive`, `reachable=false` — pass.

### Generative (profile `llm`, sau pull model)

```bash
docker compose --profile llm exec -T api python -m app.scripts.smoke_rag_generative
```

Kỳ vọng: `generation_mode=generative`, ≥1 citation hợp lệ.

### Kiểm tra thủ công API

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' | jq -r .access_token)

curl -s -X POST http://localhost:8000/api/v1/search/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"dieu 3 nghiem thu vat tu","limit":5,"max_citations":3}' | jq .
```

Checklist UI đầy đủ (extractive + generative): `docs/RAG_ANSWER_RUNBOOK.md`.

## Troubleshoot

### Ollama container OOM / bị kill

- Tăng `OLLAMA_MEMORY_LIMIT` (prod 7B CPU: **10G**).
- Giảm model (`3b` thay `7b`) hoặc chuyển GPU override.
- Giảm `RAG_LLM_MAX_CONTEXT_CHARS` / `RAG_LLM_MAX_OUTPUT_TOKENS`.
- Không chạy OCR peak và LLM cùng lúc trên RAM thấp.

### Request RAG timeout

- Tăng `RAG_LLM_TIMEOUT_SECONDS` (dev CPU: 120; không vô hạn trên prod).
- Dùng GPU hoặc model nhỏ hơn.
- Kiểm tra log API: Ollama latency.

### `/status` LLM `unavailable`

- `docker compose --profile llm ps` — service `ollama` running?
- `docker compose exec ollama ollama list` — model đã pull?
- `OLLAMA_BASE_URL` đúng (compose: `http://ollama:11434`; tách host: URL nội bộ).
- Firewall nội bộ cho port 11434.

### `/status` LLM `degraded` — model not loaded

```bash
docker compose exec ollama ollama pull qwen2.5:3b-instruct
# hoặc model khớp RAG_LLM_MODEL trong .env
```

### Answer luôn extractive dù `RAG_GENERATION_BACKEND=ollama`

- Kiểm tra `api` env: `docker compose exec api printenv RAG_GENERATION_BACKEND`
- Recreate `api` sau đổi `.env`.
- Xem `fallback_reason` trong response — thường `llm_unavailable`.

### Generative chậm trên CPU

- Chấp nhận được cho dev/smoke; prod nên GPU hoặc tách host LLM.
- `OLLAMA_NUM_PARALLEL=1` — không tăng parallel trên máy thiếu RAM.

## Liên Quan

```text
docs/RAG_ANSWER_RUNBOOK.md          — smoke extractive + checklist UI dashboard
docs/COMPOSE_RESOURCE_UPLOAD_RUNBOOK.md — limits Compose, profile llm
docs/STORAGE_BACKUP_RESTORE_RUNBOOK.md  — backup ollama_data (optional)
docs/ON_PREM_ENV_RUNBOOK.md         — production env guard
docs/DOMAIN_MODULE_DECISION.md      — prompt, validator, env contract
ROADMAP.md                          — Phase 17 sizing và tiêu chí hoàn thành
```

Mã nguồn:

- `apps/api/app/services/local_llm_service.py`
- `apps/api/app/services/rag_answer_service.py`
- `apps/api/app/services/ops_service.py` (`_get_llm_status`)
- `apps/web/components/RagAnswerPanel.vue`
- `apps/web/pages/status.vue`
