# Roadmap Phat Trien

Cap nhat lan cuoi: 2026-06-05

## Nguyen Tac

- Local/on-prem first, khong dung cloud service.
- Docker Compose first cho moi workflow dev va smoke.
- MVP first, chi mo rong khi giai quyet ro workflow nghiep vu.
- Backend giu luong `router -> service -> repository`.
- Frontend giu luong `page -> composable -> service -> API`.
- Khong tu doi stack: FastAPI, PostgreSQL, Redis, Qdrant, PaddleOCR, OpenCV, Nuxt 3, TypeScript, PrimeVue, TailwindCSS, Pinia.

## Trang Thai Hien Tai

MVP end-to-end da hoan thanh va dang chay duoc bang Docker Compose voi cac service `api`, `worker`, `web`, `postgres`, `redis`, `qdrant`.

Da hoan thanh:
- Auth local, seed admin, cookie token frontend va RBAC nhe cho admin/user.
- Upload mot file, nhieu file cung van ban va zip cung van ban.
- Quan ly metadata nghiep vu, metadata OCR tu dong va metadata manual review.
- OCR/extract cho text, markdown, docx, xlsx, PDF co text nhung, PDF/image scan bang PaddleOCR/OpenCV va VietOCR.
- Chunking van ban hanh chinh tieng Viet theo metadata phap ly, phu luc, confidence va flag `requires_review`.
- Backfill chunk metadata va reindex Qdrant payload cho DB local/dev.
- Semantic search co filter metadata nghiep vu va filter chunk nhu `section_role`, `requires_review`.
- Document detail co preview source, OCR job audit, chunks filter va action danh dau chunk da review.
- Dashboard co semantic search va admin review queue.
- Review queue da co pagination `limit/offset`, total count, filter va action review ngay tren queue.
- User audit UI cho admin xem audit log tung user.
- Smoke appendix data script da co fixture that va cleanup mac dinh.

Gioi han con lai:
- Danh sach `/documents` frontend van dung limit lon co dinh, chua co pagination count dung nghia.
- Cac smoke HTTP cho auth/search/review queue con mot phan dang chay inline, chua gom thanh workflow tai su dung duoc.
- Worker dang poll job pending truc tiep; can co co che claim/retry ro hon neu chay nhieu worker.
- Search rerank co heuristic hardcoded theo cum tu mau; can tach thanh cau hinh/benchmark.
- Chua co module nghiep vu rieng cho hop dong, cong van den/di, quyet dinh hoac phieu vat tu.
- Chua co bo cong cu admin cau hinh danh muc, model status, backup/restore va ops hardening day du.

## Lo Trinh Uu Tien

### Phase 0 - MVP Foundation

Trang thai: hoan thanh.

Muc tieu: dua he thong tu skeleton den workflow web end-to-end co the dung de upload, OCR, chunk, search, review va audit.

Da thuc hien:
- Khoi tao stack Docker Compose, backend FastAPI, frontend Nuxt 3 va data services.
- Hoan thien auth/RBAC MVP.
- Hoan thien document upload, source file, preview, reprocess va metadata.
- Hoan thien OCR pipeline local va legal-aware chunking.
- Hoan thien semantic search, Qdrant payload filters va review workflow.
- Hoan thien review queue pagination polish ngay 2026-06-05.

Tieu chi hoan thanh: workflow admin local co the upload tai lieu, doi den searchable, search, mo document nguon, review chunk va xem audit log.

### Phase 1 - Stabilize Core Workflows

Trang thai: dang uu tien tiep theo.

Muc tieu: lam cac workflow MVP on dinh hon khi du lieu tang len va bien smoke thanh kiem tra co the chay lai.

Pham vi:
- Documents pagination polish cho `/documents`.
- Smoke API auth wrapper cho review queue, semantic search va review action.
- Review queue UX polish neu queue nhieu trang can thao tac nhanh hon.
- Don dep cac smoke/script tam thanh script tai su dung duoc.

Tieu chi hoan thanh:
- Cac list lon co pagination on dinh, co total va khong trung item giua cac page.
- Smoke workflow login admin/user co the chay lai bang command ro rang.
- User/admin permission smoke bao phu cac endpoint nhay cam.

### Phase 2 - Worker Reliability Va Operations

Trang thai: chua bat dau.

Muc tieu: giam rui ro khi chay worker lau dai hoac nhieu worker trong moi truong on-prem.

Pham vi:
- Claim OCR job atomic bang database transaction/row lock.
- Chuan hoa retry, max attempts, failed reason va audit cho job.
- Them health/readiness lien quan worker va hang doi.
- Ghi tai lieu backup/restore PostgreSQL, Qdrant va uploaded source files.

Tieu chi hoan thanh:
- Hai worker chay song song khong xu ly trung mot job.
- Job loi duoc retry/co failed state ro rang.
- Co smoke/command kiem tra worker claim va retry.

### Phase 3 - Search Quality Va RAG Foundation

Trang thai: chua bat dau.

Muc tieu: tang chat luong retrieval va tao nen tang RAG local co citation ma khong phu thuoc cloud.

Pham vi:
- Tach rerank heuristic khoi logic core, dua vao cau hinh/rule rieng.
- Tao benchmark fixtures cho truy van vat tu, phu luc, dieu khoan, ngay ban hanh va don vi ban hanh.
- Danh gia embedding local va rerank local neu can.
- Thiet ke RAG answer endpoint local-only voi citation chunk/document/source page.

Tieu chi hoan thanh:
- Co bo benchmark search lap lai duoc.
- Search result giai thich duoc bang metadata/chunk citation.
- RAG neu bat dau phai tra loi kem citation, khong thay the search MVP.

### Phase 4 - Domain Modules

Trang thai: chua bat dau.

Muc tieu: mo rong tu kho van ban chung sang cac module nghiep vu thuc te cua phong vat tu.

Pham vi ung vien:
- Hop dong va phu luc hop dong.
- Cong van den/di.
- Quyet dinh, thong bao, de nghi mua sam.
- Phieu/de xuat vat tu neu can quan ly inventory workflow.

Tieu chi hoan thanh:
- Moi module co metadata rieng, filter rieng va khong pha document/search core.
- UI giu tai su dung component va service/composable hien co.
- Migration co audit fields va soft delete theo quy tac du an.

### Phase 5 - Admin Configuration Va Governance

Trang thai: chua bat dau.

Muc tieu: de admin cau hinh he thong thay vi sua code cho cac danh muc va rule co ban.

Pham vi:
- Quan ly danh muc don vi/phong ban, loai nghiep vu, loai van ban.
- Trang trang thai model/OCR/Qdrant.
- Cau hinh nhe cho threshold review, page size mac dinh va rule smoke/dev.
- Mo rong permission neu workflow nghiep vu yeu cau.

Tieu chi hoan thanh:
- Admin thay doi danh muc co audit log.
- Frontend lay option tu API thay vi hardcode nhung khong lam qua phuc tap MVP.

### Phase 6 - On-Prem Production Hardening

Trang thai: chua bat dau.

Muc tieu: chuan bi van hanh noi bo on-prem mot cach co kiem soat.

Pham vi:
- Chuan hoa `.env`, secret, CORS, file upload limits va log policy.
- Tai lieu backup/restore va migration runbook.
- Resource limits Docker Compose va storage volumes.
- Observability toi thieu: health, logs, job metrics co the xem duoc.

Tieu chi hoan thanh:
- Co runbook cai dat, nang cap, backup, restore va troubleshoot.
- Cau hinh production noi bo khong dung default secret/admin password.
