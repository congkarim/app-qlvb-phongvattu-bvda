# Task Đã Hoàn Thành: Bật Local Embedding Thật Và Benchmark Search

Trạng thái: đã triển khai.

Ngày tạo: 2026-05-31

Ngày hoàn thành: 2026-05-31

## Kết Quả

Đã triển khai:
- Chuẩn bị model local `bkai-foundation-models/vietnamese-bi-encoder` tại `models/embeddings/bkai-vietnamese-bi-encoder`.
- Tạo `.env` local để bật `EMBEDDING_BACKEND=sentence_transformers`.
- Bật `QDRANT_COLLECTION=document_chunks_bkai_768_v1`.
- Recreate `api` và `worker` bằng Docker Compose.
- Smoke test embedding thật trong worker: backend `sentence_transformers`, vector `768`, norm `1.0`.
- Reindex toàn bộ `1.584` chunks sang Qdrant collection `document_chunks_bkai_768_v1`.
- Benchmark 5 truy vấn tiếng Việt qua API semantic search.
- Cập nhật `README.md` và `PROJECT_STATUS.md`.

## Kiểm Tra Đã Chạy

Kiểm tra cấu hình trong worker:

```bash
docker compose exec -T worker python - <<'PY'
from app.core.config import get_settings
settings = get_settings()
print(settings.embedding_backend, settings.embedding_dimensions, settings.qdrant_collection)
PY
```

Kết quả:

```text
sentence_transformers 768 document_chunks_bkai_768_v1
```

Smoke test model:

```bash
docker compose exec -T worker python - <<'PY'
from app.services.embedding_service import EmbeddingService
service = EmbeddingService()
vector = service.embed("phạm vi điều chỉnh đấu thầu")
print(service.backend, len(vector), round(sum(v*v for v in vector), 4))
PY
```

Kết quả:

```text
sentence_transformers 768 1.0
```

Reindex:

```bash
docker compose exec -T worker python -m app.scripts.reindex_embeddings --batch-size 16
```

Kết quả:

```text
indexed: 1584 chunks
```

Qdrant:

```bash
curl http://localhost:6333/collections/document_chunks_bkai_768_v1
```

Kết quả chính:
- `points_count=1584`
- `vectors.size=768`
- `distance=Cosine`

API health:

```bash
curl http://localhost:8000/health
```

Kết quả:

```json
{"status":"ok"}
```

## Benchmark Search

Đã benchmark các query:
- `phạm vi điều chỉnh đấu thầu`
- `hiệu lực thi hành luật đấu thầu`
- `trách nhiệm của chủ đầu tư`
- `lựa chọn nhà thầu`
- `cơ sở dữ liệu nhà thầu`

Ghi nhận:
- Query `hiệu lực thi hành luật đấu thầu` trả đúng `Điều 95. Hiệu lực thi hành` ở top results, score khoảng `0.6735`.
- Query `trách nhiệm của chủ đầu tư` trả đúng `Điều 78. Trách nhiệm của chủ đầu tư` ở top results.
- Query `lựa chọn nhà thầu` trả đúng các điều liên quan đến ưu đãi/hình thức lựa chọn nhà thầu.
- Query `phạm vi điều chỉnh đấu thầu` có trả `Điều 1. Phạm vi điều chỉnh` trong top 5, nhưng top 1 vẫn nghiêng về nội dung cấm trong hoạt động đấu thầu.
- Query `cơ sở dữ liệu nhà thầu` trả kết quả liên quan nhưng chưa thật sắc nét, cần cải thiện bằng dedup/reranking hoặc hybrid keyword.

## Giới Hạn Còn Lại

- Dữ liệu hiện có nhiều bản upload trùng nội dung PDF/DOCX, nên top results bị duplicate.
- Search hiện chỉ vector search, chưa có hybrid keyword/BM25.
- Chưa có dedup theo `document_id`, `content_hash`, `section_title` hoặc normalized text.
- Chưa có reranking kết quả theo keyword exact match cho truy vấn pháp lý.
- API tài liệu/search hiện chưa enforce backend authorization dependency.

## Task Tiếp Theo Đề Xuất

Thêm dedup/reranking cho semantic search để giảm kết quả trùng và đẩy điều/khoản khớp truy vấn lên cao hơn.

Phạm vi gợi ý:
- Tăng số hits lấy từ Qdrant nội bộ, ví dụ `limit * 4`.
- Dedup theo `content_hash` hoặc normalized text trong `SearchService`.
- Ưu tiên kết quả có keyword exact match trong `section_title` hoặc `text`.
- Giữ response API không đổi để frontend không cần sửa nhiều.
- Benchmark lại cùng 5 query sau khi dedup/rerank.
