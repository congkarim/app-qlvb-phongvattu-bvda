# Ke Hoach Task Tiep Theo

Cap nhat lan cuoi: 2026-06-05

Tai lieu nay bam theo `ROADMAP.md` va trang thai da ghi trong `PROJECT_STATUS.md`. Muc uu tien hien tai la on dinh core workflow sau khi MVP va review queue pagination da hoan thanh.

## Task Vua Hoan Thanh

Queue pagination polish: hoan thanh ngay 2026-06-05.

Ket qua chinh:
- Backend `GET /api/v1/documents/chunks/review-queue` tra `items`, `total`, `limit`, `offset`.
- Repository co count matching cung filter `section_role`, `document_id`, `max_confidence`.
- Query queue co sort on dinh theo confidence, `updated_at` va `DocumentChunk.id`.
- Dashboard admin hien thi tong so item, khoang item hien tai, nut `Truoc/Sau`, giu filter khi chuyen trang va refresh hop ly sau action `Da review`.
- Frontend van giu dung luong `page -> composable -> service -> API`.

Da kiem tra:
- Backend compile pass.
- Frontend build pass, chi con warning chunk PrimeVue lon nhu truoc.
- Appendix smoke pass.
- Pagination smoke pass voi hai page khong trung item.
- User forbidden smoke pass voi review queue tra `403`.

## Uu Tien 1 - Documents Pagination Polish

Trang thai: de xuat lam tiep theo.

Muc tieu:
- Thay limit co dinh tren `/documents` bang pagination co total count de danh sach van ban dung duoc khi data tang.
- Giu luong frontend `page -> composable -> service -> API`.
- Giu backend `router -> service -> repository`.

Pham vi backend:
- Mo rong schema response danh sach document thanh object co `items`, `total`, `limit`, `offset`.
- Giu cac filter/search/sort hien co cua danh sach document.
- Them repository count document matching dung cung filter voi list.
- Tach helper filter neu can de list/count khong lech logic.
- Them sort tie-breaker bang `Document.id` de pagination on dinh.
- Giu endpoint permission hien co, khong them migration neu khong can.

Pham vi frontend:
- Cap nhat type response document list.
- Cap nhat `document.service.ts` nhan response pagination.
- Cap nhat composable quan ly `documents`, `documentsTotal`, `documentsLimit`, `documentsOffset`.
- Cap nhat page `/documents` de hien thi tong so, khoang item, nut trang truoc/sau hoac paginator PrimeVue neu phu hop.
- Reset offset ve `0` khi doi search/filter/sort.
- Giu refresh action va empty/loading/error state hien co.

Tieu chi chap nhan:
- Danh sach document page 1/page 2 khong trung item khi du lieu du lon.
- Search/filter/sort van hoat dong sau khi them pagination.
- UI khong goi API truc tiep trong component ngoai service/composable hien co.
- Khong pha document detail, upload, search dashboard.

Kiem tra can chay:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/schemas/document.py apps/api/app/repositories/document_repository.py apps/api/app/services/document_service.py apps/api/app/routers/documents.py
docker compose run --rm --no-deps web npm run build
python3 <documents pagination smoke script>
git diff --check
```

## Uu Tien 2 - Smoke API Auth Wrapper

Trang thai: de xuat sau documents pagination.

Muc tieu:
- Chuyen cac smoke HTTP inline thanh script tai chay duoc, co login admin/user va cleanup ro rang.
- Giam rui ro regression cho review queue, semantic search va review action.

Pham vi:
- Tao script smoke API workflow trong `apps/api/app/scripts/`.
- Dung admin local de login va lay token.
- Tao user thuong tam neu can de kiem tra permission.
- Seed document/chunk smoke toi thieu hoac tai su dung appendix fixture hien co.
- Kiem tra review queue admin thanh cong va user thuong bi `403`.
- Kiem tra semantic search voi filter co ban va filter `section_role=appendix`.
- Kiem tra action review chunk cap nhat DB va Qdrant payload.
- Cleanup user/document/chunk/Qdrant point sau khi chay, co option `--keep-data` neu can debug UI.

Tieu chi chap nhan:
- Mot command smoke co the chay lai tren Docker Compose dang active.
- Script fail fast voi error message ro endpoint nao loi.
- Du lieu smoke khong de lai rac khi chay mac dinh.

Kiem tra can chay:

```bash
PYTHONPYCACHEPREFIX=/tmp/qlvb-pycache PYTHONPATH=apps/api python3 -m py_compile apps/api/app/scripts/smoke_api_workflows.py
docker compose exec -T api python -m app.scripts.smoke_api_workflows
git diff --check
```

## Uu Tien 3 - Review Queue UX Polish

Trang thai: tuy chon, lam khi queue nhieu trang can thao tac nhanh hon.

Muc tieu:
- Cai thien thao tac admin tren queue dai ma khong lam phuc tap dashboard.

Pham vi:
- Danh gia UI hien tai `Truoc/Sau` co du dung khong.
- Neu can, thay bang PrimeVue paginator hoac them current page/page count.
- Giu filter queue hien co: tat ca, phu luc, unknown, confidence thap, document id.
- Dam bao action `Da review` khong day admin ve sai page.

Tieu chi chap nhan:
- Admin biet dang o page nao va tong so item con lai.
- Chuyen trang khong mat filter.
- UI compact, khong tao card long nhau.

Kiem tra can chay:

```bash
docker compose run --rm --no-deps web npm run build
python3 <review queue pagination smoke script>
git diff --check
```

## Phase 2 - Worker Reliability Va Operations

Trang thai: chua bat dau.

Muc tieu:
- Lam OCR worker an toan hon khi chay lau dai hoac chay nhieu worker.

Ke hoach chi tiet:
- Khao sat hien trang worker polling pending job va repository update job status.
- Them co che claim atomic bang transaction/row lock de tranh hai worker xu ly cung job.
- Chuan hoa `attempts`, retry policy, failed reason va job audit.
- Them smoke hoac integration check voi hai worker/process neu kha thi.
- Viet runbook ngan cho restart worker, job failed va reprocess.

Tieu chi chap nhan:
- Hai worker song song khong xu ly trung mot OCR job.
- Job failed co error ro va khong bi lap vo han.
- Reprocess van tao job dung va detail page van polling dung status.

## Phase 3 - Search Quality Va RAG Foundation

Trang thai: chua bat dau.

Muc tieu:
- Tang chat luong retrieval va chuan bi RAG local co citation.

Ke hoach chi tiet:
- Trich xuat cac heuristic rerank hardcoded thanh module/rule rieng.
- Tao bo benchmark query fixture cho vat tu, phu luc, dieu khoan, ngay ban hanh va don vi ban hanh.
- Them command chay benchmark search local va report top-k.
- Danh gia embedding local/rerank local neu can, khong dung cloud.
- Thiet ke API RAG local-only sau khi benchmark search on dinh.

Tieu chi chap nhan:
- Search core khong tron cac rule mau hardcoded kho maintain.
- Benchmark co the chay lai va so sanh thay doi ranking.
- Cau tra loi RAG neu them phai co citation chunk/document/source.

## Phase 4 - Domain Modules

Trang thai: chua bat dau.

Muc tieu:
- Mo rong tu document repository chung sang cac module nghiep vu cua phong vat tu.

Ke hoach chi tiet:
- Chon mot module dau tien co gia tri cao nhat, vi du hop dong/phu luc hop dong hoac cong van den/di.
- Dinh nghia metadata rieng nhung van lien ket document core.
- Tao migration co UUID primary key, audit fields va soft delete.
- Them backend theo `router -> service -> repository`.
- Them frontend theo `page -> composable -> service -> API`.
- Tai su dung component list/filter/detail neu co the.

Tieu chi chap nhan:
- Module moi khong pha upload/OCR/search core.
- Metadata module co the filter/search duoc.
- UI co workflow nghiep vu ro, khong chi la landing page.

## Phase 5 - Admin Configuration Va Governance

Trang thai: chua bat dau.

Muc tieu:
- De admin quan ly danh muc va cau hinh nhe khong can sua code.

Ke hoach chi tiet:
- Thiet ke danh muc can co: don vi/phong ban, loai nghiep vu, loai van ban.
- Them CRUD admin co audit log.
- Cap nhat frontend option lay tu API thay vi hardcode cho cac field phu hop.
- Them trang status toi thieu cho OCR/model/Qdrant.
- Neu can, mo rong permission nhung giu RBAC don gian.

Tieu chi chap nhan:
- Admin thay doi danh muc co audit log.
- UI form dung option tu API va van co fallback hop ly.
- Khong bien admin config thanh framework phuc tap.

## Phase 6 - On-Prem Production Hardening

Trang thai: chua bat dau.

Muc tieu:
- Chuan bi van hanh noi bo on-prem co kiem soat.

Ke hoach chi tiet:
- Chuan hoa `.env`, secret, CORS va default admin password policy.
- Tai lieu storage volumes cho PostgreSQL, Qdrant va uploads.
- Viet backup/restore runbook.
- Them health/readiness check can thiet.
- Kiem tra upload limits, log policy va resource limits Docker Compose.

Tieu chi chap nhan:
- Cai dat moi khong dung secret/password mac dinh trong production noi bo.
- Co tai lieu backup/restore va troubleshoot.
- Health check phan biet service song voi service san sang xu ly workflow.
