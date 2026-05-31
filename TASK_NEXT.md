# Task Đã Hoàn Thành: Sửa Trích Xuất PDF Tiếng Việt

Trạng thái: đã triển khai.

Ngày tạo: 2026-05-31

Ngày hoàn thành: 2026-05-31

## Kết Quả

Đã triển khai:
- PDF có text nhúng được trích xuất trực tiếp bằng `pypdfium2` trước khi OCR.
- Page PDF không có text hoặc quá ít text vẫn fallback sang render ảnh và PaddleOCR.
- Text PDF native được clean theo dòng để giữ cấu trúc đọc tốt hơn trên màn chi tiết.
- README và PROJECT_STATUS đã cập nhật workflow PDF mới.

## Kiểm Tra Đã Chạy

```bash
docker compose exec -T worker python -m py_compile /app/app/services/document_content_service.py
```

```bash
docker compose exec -T worker python - <<'PY'
from pathlib import Path
from app.services.document_content_service import DocumentContentService
path = Path('/data/uploads/3fb4e2b5-78ea-412e-8c7e-7feea777b831_Văn-bản-hợp-nhất-74-VBHN-VPQH.pdf')
pages = DocumentContentService().extract_pages(path, path.name)
print(len(pages), pages[0].confidence)
print(pages[0].text[:120])
PY
```

Kết quả với file `Văn-bản-hợp-nhất-74-VBHN-VPQH.pdf`: đọc được 90 page, page đầu có `confidence=1.0` và giữ dấu tiếng Việt như `CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM`.

## Giới Hạn Còn Lại

- Các document PDF đã xử lý trước fix vẫn đang lưu text OCR cũ; cần upload lại hoặc thêm cơ chế reprocess để sinh lại page/chunk.
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
