# OCR Text Chunking

Module chunking OCR text cho văn bản hành chính tiếng Việt, tối ưu retrieval/RAG.

## Pipeline

```text
OCR text/layout
-> normalize tiếng Việt nhẹ
-> detect doc_type theo hình thức văn bản
-> map doc_type vào nhóm A/B/C/D/E
-> chọn chunking strategy
-> tạo structural chunks
-> tạo retrieval chunks nếu chunk quá dài
-> gắn metadata
-> fallback nếu OCR lỗi/mất bố cục
-> trả JSON chuẩn
```

## Cách Dùng

```python
from app.services.ocr_chunking import OCRDocument, OCRPage, chunk_document

document = OCRDocument(
    doc_id="document-id",
    pages=[
        OCRPage(page_number=1, text="QUYẾT ĐỊNH\nĐiều 1. ...", confidence=0.91),
    ],
    layout_confidence=0.8,
)

chunks = chunk_document(document)
payload = [chunk.to_dict() for chunk in chunks]
```

## Thiết Kế

- `mappings.py`: mapping nhãn `doc_type` sang nhóm chunk A/B/C/D/E.
- `anchors.py`: regex và anchor phrases cho từng nhóm.
- `schemas.py`: interface input/output bằng dataclass có type hints.
- `pipeline.py`: hàm chính `chunk_document(input: OCRDocument) -> list[Chunk]`.
- `adapter.py`: map output `Chunk` sang payload lưu `document_chunks` và metadata Qdrant.

Worker hiện dùng module này mặc định qua `CHUNKING_BACKEND=ocr_chunking`. Có thể rollback tạm thời về chunking cũ bằng `CHUNKING_BACKEND=legacy`.

## Quy Tắc Chính

- Nhóm A (`NQ`, `QĐ`, `CT`, `QC`, `QYĐ`): ưu tiên cắt theo `Chương/Điều/Khoản/Điểm`; `Điều` ngắn giữ nguyên, `Khoản` dài mới tạo retrieval child chunk.
- Nhóm B (`TB`, `HD`, `CTr`, `KH`, `PA`, `ĐA`, `DA`, `BC`, `TTr`, `CĐ`, `CV`): cắt theo `I/II/III`, `1/2/3`, anchor nghiệp vụ, nhiệm vụ, timeline, kinh phí và bảng.
- Nhóm C (`BB`, `HĐ`, `BGN`, `BTT`): hợp đồng cắt theo `Điều`; biên bản/bàn giao/thanh toán cắt theo thời gian, thành phần, nội dung, bảng, kết luận, chữ ký.
- Nhóm D (`GUQ`, `GM`, `GGT`, `GNP`, `PG`, `PC`, `PB`, `TCg`): giấy tờ ngắn giữ một chunk toàn văn nếu dưới 1000 token.
- Nhóm E (`UNKNOWN`): fallback theo page/paragraph/heading/table candidate, chunk 500-900 token và đánh `requires_review`.

## Test

Chạy từ root repo:

```bash
PYTHONPATH=apps/api python3 -m unittest app.services.ocr_chunking.tests.test_pipeline
```
