# Task Đã Hoàn Thành: Tích Hợp Local Embedding Backend

Trạng thái: đã triển khai phần code và cấu hình.

Ngày tạo: 2026-05-31

Ngày hoàn thành: 2026-05-31

## Kết Quả

Đã triển khai:
- Thêm cấu hình embedding backend, model name/path, device, dimensions, batch size và local-files-only.
- `EmbeddingService` hỗ trợ `fake` cho dev và `sentence_transformers` cho model local/on-prem.
- `QdrantService` kiểm tra vector dimensions của collection hiện có và fail rõ nếu sai cấu hình.
- Docker Compose mount `./models:/models` cho `api` và `worker`.
- Thêm script `python -m app.scripts.reindex_embeddings` để reindex chunks hiện có sang Qdrant collection đang cấu hình.
- Cập nhật README với cách chuẩn bị model local, bật env và test semantic search.

## Kiểm Tra Cần Chạy Sau Khi Build Image

```bash
docker compose build api worker
```

```bash
docker compose up -d postgres redis qdrant api worker
```

Với fake embedding/dev:

```bash
docker compose exec -T worker python -m app.scripts.reindex_embeddings --batch-size 16 --dry-run
```

Với local embedding thật:

```bash
docker compose exec -T worker python -m app.scripts.reindex_embeddings --batch-size 16
```

Search kiểm tra:

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query":"phạm vi điều chỉnh đấu thầu","limit":5}'
```

## Giới Hạn Còn Lại

- Cần chuẩn bị model thật trong `models/embeddings/bkai-vietnamese-bi-encoder` trước khi bật `EMBEDDING_BACKEND=sentence_transformers`.
- Chưa benchmark chất lượng giữa `bkai-foundation-models/vietnamese-bi-encoder` và model nhẹ hơn.
- Metadata filters search còn tối thiểu.
- API tài liệu/search hiện chưa enforce backend authorization dependency.

## Task Tiếp Theo Đề Xuất

Chuẩn bị model local, bật env `sentence_transformers`, reindex dữ liệu hiện có và benchmark truy vấn tiếng Việt thực tế.

Phạm vi gợi ý:
- Copy model vào `models/embeddings/bkai-vietnamese-bi-encoder`.
- Tạo `.env` local với `QDRANT_COLLECTION=document_chunks_bkai_768_v1`.
- Build lại `api` và `worker`.
- Chạy reindex embeddings.
- So sánh top results với các truy vấn nghiệp vụ: đấu thầu, hiệu lực thi hành, phạm vi điều chỉnh, trách nhiệm cơ quan.
