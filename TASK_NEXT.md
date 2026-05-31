# Task Tiếp Theo: Bật Local Embedding Thật Và Benchmark Search

Trạng thái: lên kế hoạch.

Ngày tạo: 2026-05-31

## Mục Tiêu

Bật embedding model local/on-prem thật, reindex dữ liệu hiện có sang Qdrant collection version mới và benchmark semantic search tiếng Việt để xác nhận score có ý nghĩa hơn fake embedding.

## Ràng Buộc Không Đổi

- Không dùng cloud service hoặc API LLM bên ngoài.
- Không đổi stack cố định: FastAPI, PostgreSQL, Redis, Qdrant, PaddleOCR, OpenCV, Nuxt 3, PrimeVue, TailwindCSS, Pinia.
- Docker Compose first.
- MVP first, không over-engineering.
- Backend giữ kiến trúc `router -> service -> repository`.
- Frontend giữ kiến trúc `page -> composable -> service -> API`.
- Không commit model files hoặc runtime artifacts.

## Phạm Vi Triển Khai

### 1. Chuẩn Bị Model Local

Model chính:

```text
bkai-foundation-models/vietnamese-bi-encoder
```

Thư mục local:

```text
models/embeddings/bkai-vietnamese-bi-encoder
```

Yêu cầu:
- Model phải nằm local trước khi bật `EMBEDDING_BACKEND=sentence_transformers`.
- Runtime không phụ thuộc tải model từ internet.
- Thư mục `models/` không được commit.
- Nếu model chưa sẵn sàng và `ALLOW_FAKE_EMBEDDINGS=false`, API/worker phải fail rõ ràng.

### 2. Tạo Cấu Hình `.env` Local

Nội dung dự kiến:

```env
EMBEDDING_BACKEND=sentence_transformers
EMBEDDING_MODEL_NAME=bkai-foundation-models/vietnamese-bi-encoder
EMBEDDING_MODEL_PATH=/models/embeddings/bkai-vietnamese-bi-encoder
EMBEDDING_DEVICE=cpu
EMBEDDING_DIMENSIONS=768
EMBEDDING_BATCH_SIZE=16
EMBEDDING_LOCAL_FILES_ONLY=true
ALLOW_FAKE_EMBEDDINGS=false
QDRANT_COLLECTION=document_chunks_bkai_768_v1
```

Ghi chú:
- Không dùng lại collection fake/current khi đổi dimensions.
- Mỗi model hoặc vector dimension phải dùng collection version riêng.

### 3. Recreate Services Với Config Mới

```bash
docker compose up -d api worker
```

Kiểm tra logs:

```bash
docker compose logs --tail=100 api
docker compose logs --tail=100 worker
```

### 4. Smoke Test Model Trong Worker

```bash
docker compose exec -T worker python - <<'PY'
from app.services.embedding_service import EmbeddingService
service = EmbeddingService()
vector = service.embed("phạm vi điều chỉnh đấu thầu")
print(service.backend, len(vector), round(sum(v*v for v in vector), 4))
PY
```

Kỳ vọng:

```text
sentence_transformers 768 1.0
```

### 5. Reindex Toàn Bộ Chunks

```bash
docker compose exec -T worker python -m app.scripts.reindex_embeddings --batch-size 16
```

Kiểm tra sau reindex:
- Qdrant có collection `document_chunks_bkai_768_v1`.
- Vector size của collection là `768`.
- Số point trong Qdrant tương ứng số chunks đã index.
- Search API không còn dùng collection fake mặc định.

### 6. Benchmark Search Tiếng Việt

Bộ query tối thiểu:

```text
phạm vi điều chỉnh đấu thầu
hiệu lực thi hành luật đấu thầu
trách nhiệm của chủ đầu tư
lựa chọn nhà thầu
cơ sở dữ liệu nhà thầu
```

Lệnh test:

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query":"phạm vi điều chỉnh đấu thầu","limit":5}'
```

Ghi nhận cho từng query:
- Top 5 chunks có liên quan nghiệp vụ không.
- Score có phân tách tốt hơn fake embedding không.
- Có duplicate document/chunk quá nhiều không.
- Có cần task sau để lọc trùng theo `document_id`, `content_hash` hoặc `section_title` không.

### 7. Cập Nhật Tài Liệu

Cập nhật sau benchmark:
- `PROJECT_STATUS.md`: trạng thái model local, reindex và kết quả benchmark.
- `TASK_NEXT.md`: chuyển task này sang đã hoàn thành và ghi task kế tiếp.
- `README.md`: chỉnh hướng dẫn nếu phát hiện bước setup cần rõ hơn.

### 8. Commit

Chạy kiểm tra:

```bash
git status --short
git diff --check
git diff --stat
```

Commit dự kiến:

```bash
git add PROJECT_STATUS.md TASK_NEXT.md README.md
git commit -m "chore: benchmark local Vietnamese embeddings"
```

## Tiêu Chí Hoàn Thành

- Worker load model local thành công.
- Query embedding trả vector 768 chiều và norm xấp xỉ `1.0`.
- Reindex chạy xong không lỗi.
- Search API trả kết quả từ collection `document_chunks_bkai_768_v1`.
- Có benchmark tối thiểu 5 query tiếng Việt.
- Không dùng cloud service, không đổi stack, không commit model files.

## Rủi Ro Và Theo Dõi

- Máy local CPU có thể reindex chậm; giảm `EMBEDDING_BATCH_SIZE` nếu thiếu RAM.
- Nếu Qdrant báo dimension mismatch, kiểm tra `QDRANT_COLLECTION` đã đổi sang collection version mới chưa.
- Nếu kết quả search duplicate nhiều, task sau nên thêm dedup/reranking ở `SearchService`.
- Nếu model BKAI quá nặng cho máy local, task sau benchmark model nhẹ hơn nhưng vẫn local/on-prem.
