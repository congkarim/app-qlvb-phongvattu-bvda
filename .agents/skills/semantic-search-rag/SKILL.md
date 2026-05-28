---
name: semantic-search-rag
description: Thiết kế semantic search và RAG local với chunking văn bản pháp lý, embedding local và Qdrant.
---

# Semantic Search RAG Skill

## Responsibilities

- Thiết kế chunking cho văn bản pháp lý tiếng Việt.
- Tạo embedding bằng model local/on-prem.
- Lưu vector trong Qdrant kèm metadata đủ lọc.
- Xây dựng semantic search, hybrid search khi cần và context retrieval cho RAG.

## Rules

- Không dùng embedding hoặc LLM cloud service.
- Chunk phải giữ ngữ cảnh pháp lý theo Điều/Khoản/Mục khi có thể.
- Qdrant payload phải đủ metadata để filter theo loại văn bản, phòng ban, ngày, trạng thái và entity nghiệp vụ.
- Không đưa dữ liệu đã soft delete vào kết quả search mặc định.
- Retrieval phải có pagination/limit rõ ràng.

## Architecture

```text
OCR text -> legal-aware chunking -> local embedding -> Qdrant upsert -> search/retrieval
```

## Stack

- Local embedding model
- Qdrant
- PostgreSQL document metadata
- FastAPI search APIs

## Modules

- Chunk parser for legal structure.
- Embedding service.
- Qdrant collection manager.
- Vector upsert/delete sync.
- Metadata filter builder.
- Search ranking and response formatting.
- RAG context builder.

## Chunk Rules

- Ưu tiên chunk theo `Điều`, `Khoản`, `Mục`, tiêu đề, phụ lục.
- Kích thước chunk mục tiêu: 800-1200 tokens.
- Overlap: 100-150 tokens.
- Không cắt ngang câu nếu có thể tránh.
- Chunk phải lưu `document_id`, `page_from`, `page_to`, `chunk_index`, `section_title` nếu có.
- Chunk phải có checksum hoặc content hash để tránh re-embed không cần thiết.

## Coding Conventions

- Tách rõ embedding generation và vector storage.
- Qdrant collection schema phải được quản lý có version.
- Metadata filtering phải được build có kiểm soát, không ghép query tùy tiện.
- Khi document bị soft delete, search mặc định phải loại bỏ chunks tương ứng.
- Khi OCR text thay đổi, phải invalidate hoặc update lại chunks và vectors liên quan.
- Search response phải trả source metadata để người dùng mở lại văn bản gốc.
