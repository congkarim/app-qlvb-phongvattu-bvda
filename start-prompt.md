# TASK: START MVP IMPLEMENTATION FOR LEGAL DOCUMENT AI SYSTEM

Đọc:

* AGENTS.md
* toàn bộ .agents/skills/*

và bắt đầu triển khai MVP thực tế.

## Mục tiêu MVP

Xây dựng skeleton chạy được end-to-end:

Upload file
→ lưu file
→ tạo OCR job
→ OCR skeleton
→ lưu text
→ tạo chunks
→ tạo embedding skeleton
→ lưu Qdrant
→ search semantic skeleton

---

# 1. Stack cố định

Backend:

* FastAPI
* PostgreSQL
* Redis
* Qdrant
* PaddleOCR
* OpenCV

Frontend:

* Nuxt 3
* TypeScript
* PrimeVue
* TailwindCSS
* Pinia

Deploy:

* Docker Compose

---

# 2. Cấu trúc monorepo cần tạo

legal-doc-ai/
├── apps/
│   ├── api/
│   ├── worker/
│   └── web/
├── packages/
├── docker/
├── .agents/
├── AGENTS.md
├── docker-compose.yml
└── README.md

---

# 3. Backend structure

apps/api/
├── app/
│   ├── main.py
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── routers/
│   └── workers/
└── alembic/

Tạo:

* FastAPI app
* health endpoint
* auth skeleton
* upload API
* document API
* OCR job skeleton
* semantic search skeleton

---

# 4. Frontend structure

apps/web/
├── pages/
├── components/
├── composables/
├── services/
├── stores/
├── types/
└── utils/

Tạo:

* login page
* dashboard page
* documents list page
* upload page
* document detail page

Dùng:

* PrimeVue
* TailwindCSS
* Pinia

---

# 5. Database

Tạo migration ban đầu cho:

* users
* departments
* documents
* document_pages
* document_chunks
* ocr_jobs

Tất cả:

* UUID
* created_at
* updated_at
* deleted_at

---

# 6. Docker Compose

Tạo:

* api
* web
* worker
* postgres
* redis
* qdrant

Volumes:

* postgres_data
* qdrant_data
* uploads_data

---

# 7. OCR pipeline skeleton

Tạo worker flow:

upload
→ create ocr job
→ simulate OCR
→ save page text
→ mark searchable

Chưa cần OCR hoàn chỉnh ngay.

---

# 8. Semantic search skeleton

Tạo:

* embedding service interface
* qdrant service
* semantic search endpoint

Có thể dùng fake embedding trước.

---

# 9. README

README phải hướng dẫn:

* cách chạy Docker
* cách migrate DB
* cách start backend/frontend
* cách test upload API
* cách test semantic search

---

# 10. Quy tắc cực quan trọng

* Ưu tiên skeleton chạy được.
* Không over-engineering.
* Không thêm microservices.
* Không thêm Kubernetes.
* Không thêm CI/CD lúc này.
* Không thêm cloud dependency.

---

# 11. Sau mỗi bước lớn

Phải báo:

* file nào được tạo
* mục đích file
* command để test
* bước tiếp theo
