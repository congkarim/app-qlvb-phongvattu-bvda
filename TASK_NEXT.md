# Task Đã Hoàn Thành: Sửa Lỗi Section Title Quá Dài Khi Chunking

Trạng thái: đã triển khai.

Ngày tạo: 2026-05-31

Ngày hoàn thành: 2026-05-31

## Kết Quả

Đã triển khai:
- Sửa regex tách `Điều N` trong `ChunkingService` để không lấy cả đoạn dài làm `section_title`.
- Giới hạn `section_title` sinh ra dưới giới hạn `varchar(512)` của PostgreSQL.
- Reprocess các job VBHN từng failed vì `value too long for type character varying(512)`.
- PROJECT_STATUS đã cập nhật trạng thái fix.

## Kiểm Tra Đã Chạy

```bash
docker compose exec -T worker python -m py_compile /app/app/services/chunking_service.py
```

```bash
docker compose exec -T worker python - <<'PY'
from app.services.chunking_service import ChunkingService
text = 'Điều 3 của Luật này để: 2 thuế nhập khẩu, Luật Đầu tư, Luật Đầu tư công, Luật Quản lý, sử dụng tài sản công ' * 30
chunks = ChunkingService().create_chunks(text)
print(max(len(chunk['section_title'] or '') for chunk in chunks))
PY
```

Kết quả DB: các document `Văn-bản-hợp-nhất-74-VBHN-VPQH` lỗi cũ đã chuyển `searchable/completed`; không còn job có error `value too long for type character varying(512)`.

## Giới Hạn Còn Lại

- PaddleOCR tiếng Việt vẫn phụ thuộc model Latin khi gặp PDF scan/image scan nên chất lượng dấu có thể thấp hơn PDF text-native.
- Embedding vẫn là fake deterministic embedding.

## Task Tiếp Theo Đề Xuất

Tích hợp local embedding model thật để score semantic search có ý nghĩa hơn.

Phạm vi gợi ý:
- Chọn embedding model local/on-prem phù hợp tiếng Việt.
- Thêm config model path/name và vector dimensions.
- Điều chỉnh Qdrant collection strategy khi dimensions thay đổi.
- Giữ fallback rõ ràng nếu model chưa được tải/cấu hình.
- Cập nhật README với cách chuẩn bị model và test semantic search.
