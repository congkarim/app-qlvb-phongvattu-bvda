# RAG Answer Runbook

Cập nhật lần cuối: 2026-06-07

Hướng dẫn tái chạy smoke API và kiểm tra thủ công panel **Hỏi đáp (RAG)** trên dashboard sau thay đổi search/RAG/frontend.

Hệ thống hỗ trợ hai chế độ generation:

| Chế độ | Cấu hình | Smoke |
| --- | --- | --- |
| **Extractive** (mặc định) | `RAG_GENERATION_BACKEND=extractive` | `smoke_rag_answer` |
| **Generative (local Ollama)** | `RAG_GENERATION_BACKEND=ollama` + `--profile llm` + pull model | `smoke_rag_generative` |

Bật/tắt LLM, sizing prod, GPU, troubleshoot: **`docs/RAG_LLM_RUNBOOK.md`**.

## Điều Kiện

- Stack Docker Compose đang chạy: `api`, `postgres`, `redis`, `qdrant` (và `web` nếu kiểm tra UI).
- Generative: thêm `ollama` qua `docker compose --profile llm up -d` và pull model (xem runbook LLM).
- API healthy: `curl http://localhost:8000/health/ready`.
- Embedding backend cấu hình nhất quán giữa API và worker (mặc định dev: fake deterministic hoặc `sentence-transformers` local).

## Smoke API Extractive (Bắt Buộc Regression)

Script seed benchmark fixture, gọi `POST /api/v1/search/answer` qua HTTP thật, kiểm tra grounded answer + citation + fallback `insufficient_evidence`, cleanup mặc định.

**Không cần Ollama** — chạy với stack mặc định (`RAG_GENERATION_BACKEND=extractive`).

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer
```

Kết quả mong đợi (JSON in ra stdout):

- `grounded_citations` > 0
- `expected_chunk_id` có giá trị UUID
- `fallback_reason` = `insufficient_evidence`
- `cleanup` = `removed`

Giữ dữ liệu fixture để kiểm tra UI thủ công:

```bash
docker compose exec -T api python -m app.scripts.smoke_rag_answer --keep-data
```

Gỡ fixture sau khi xong (nếu cần): chạy lại smoke không `--keep-data`, hoặc xóa document benchmark thủ công trong DB.

Tuỳ chọn — gọi API trực tiếp sau khi login:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' | jq -r .access_token)

curl -s -X POST http://localhost:8000/api/v1/search/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"dieu 3 nghiem thu vat tu","limit":5,"max_citations":3}' | jq .
```

Extractive response: `generation_mode=extractive` (hoặc field absent, tương đương extractive).

## Smoke API Generative (Khi Bật Profile `llm`)

Sau khi cấu hình Ollama và pull model (`docs/RAG_LLM_RUNBOOK.md`):

```bash
docker compose --profile llm exec -T api python -m app.scripts.smoke_rag_generative
```

Kỳ vọng: `generation_mode=generative`, citations hợp lệ.

## Kiểm Tra UI Dashboard (Thủ Công)

Mở `http://localhost:3000` (hoặc URL `web` nội bộ). Đăng nhập admin hoặc user thường.

### Chuẩn bị dữ liệu

1. Chạy smoke với `--keep-data` (xem trên), **hoặc** dùng văn bản searchable sẵn có trong hệ thống.
2. Vào `/dashboard`.

### Checklist RAG Q&A

| # | Bước | Kỳ vọng |
| --- | --- | --- |
| 0 | (Generative) Badge trên panel sau **Hỏi** | **Extractive** hoặc **Generative (local)**; có thể thấy `model_name`, `latency_ms` |
| 1 | Nhập câu hỏi `dieu 3 nghiem thu vat tu` (với fixture smoke) → **Hỏi** | Loading “Đang tổng hợp câu trả lời…”, nút **Hỏi** disabled khi pending; sau đó khối **Câu trả lời** (nền xanh nhạt), `Độ tin cậy` hiển thị |
| 2 | Xem danh sách **Nguồn trích dẫn** | Có ít nhất một citation: `quote`, metadata (số VB/trang/section), link **Mở văn bản** → `/documents/{id}` |
| 3 | Nhập câu hỏi không liên quan dữ liệu (ví dụ `noi dung khong ton tai trong he thong`) → **Hỏi** | `Message` cảnh báo vàng; khối **Giải thích** (không gắn nhãn “Câu trả lời” chắc chắn); không có answer grounded giả |
| 4 | Đổi một filter metadata (ví dụ `doc_group`) | Hint “Bộ lọc đã thay đổi…”; kết quả RAG cũ bị xóa |
| 5 | Bấm **Hỏi** lại sau khi đổi filter | Request mới, không lỗi console/API |
| 6 | Bấm **Xóa** | Input và kết quả RAG được reset |
| 7 | (Tùy chọn) Tắt Ollama, `RAG_GENERATION_BACKEND=ollama` → **Hỏi** lại | Message info “Mô hình local không sẵn sàng…”; answer extractive nếu có căn cứ; badge **Extractive** |

### Checklist trang `/status`

| # | Bước | Kỳ vọng |
| --- | --- | --- |
| 1 | Mở `/status` (admin) | Card **LLM (RAG)**: backend, model, reachable |
| 2 | Extractive-only stack | `generation_backend=extractive`, `reachable=false` — không lỗi trang |
| 3 | Profile `llm` + model loaded | `status=ok`, `model_loaded=true` |

### Checklist regression Semantic Search

| # | Bước | Kỳ vọng |
| --- | --- | --- |
| 1 | Trong card **Semantic search**, nhập `nghiem thu` → **Search** | Có kết quả hoặc thông báo “Không có kết quả”; không lỗi API |
| 2 | Đổi filter hợp đồng (`contract_number`, `supplier_name`) → search lại | Kết quả/filter hoạt động như trước khi có panel RAG |

## Build Frontend (Sau Thay Đổi UI)

```bash
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps \
  -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
```

Container `web` mặc định giới hạn 512M — build SSR có thể OOM nếu không tăng `WEB_MEMORY_LIMIT`.

## Liên Quan

- Generative / Ollama ops: `docs/RAG_LLM_RUNBOOK.md`
- Benchmark fixture: `apps/api/app/scripts/benchmark_search_fixtures.py`
- Service RAG: `apps/api/app/services/rag_answer_service.py`
- UI: `apps/web/pages/dashboard.vue`, `apps/web/components/RagAnswerPanel.vue`
- Unit test: `apps/api/app/services/tests/test_rag_answer_service.py`
