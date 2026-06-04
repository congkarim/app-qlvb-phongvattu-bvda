# Task Tiếp Theo: Admin UX Polish Và Auth Scope MVP

Trạng thái: đề xuất.

Ngày cập nhật: 2026-06-04

## Task Vừa Hoàn Thành

Đã kiểm tra browser workflow reprocess end-to-end và bổ sung auth guard backend cho API tài liệu/search.

Kết quả chính:
- Thêm dependency `get_current_user` để validate Bearer JWT và load user active từ DB.
- Gắn auth dependency vào routers:
  - `/api/v1/documents`
  - `/api/v1/search`
- Giữ `/health` public.
- Frontend vẫn gọi API được nhờ cookie `auth_token` và API client tự gắn `Authorization`.
- Headless Chrome đã mở document detail, nhập reason và click `Reprocess` từ UI.
- Job reprocess tạo từ UI chạy xong và audit reason hiển thị trong detail API.
- Search sau reprocess vẫn trả document nguồn đúng top 1.

Đã kiểm tra:

```bash
docker compose run --rm --no-deps api python -m py_compile /app/app/dependencies.py /app/app/repositories/user_repository.py /app/app/routers/documents.py /app/app/routers/search.py
docker compose up -d --build api worker web
curl -fsS http://localhost:8000/health
curl -sS -o /tmp/documents_no_token.json -w '%{http_code}\n' http://localhost:8000/api/v1/documents
curl -sS -o /tmp/search_no_token.json -w '%{http_code}\n' -X POST http://localhost:8000/api/v1/search/semantic -H 'Content-Type: application/json' -d '{"query":"Số 72 UBND KT","limit":3}'
docker compose run --rm --no-deps web npm run build
docker compose config --quiet
git diff --check
```

Kết quả verify:
- `/api/v1/documents` và `/api/v1/search/semantic` trả `401` khi thiếu token.
- Token admin local gọi documents/search thành công.
- UI-created job `99dcdfd8-cbf1-4332-a8b8-298d1a30abcf` completed, attempts `1`, reason `headless browser UI reprocess 2026-06-04 retry`.
- Search `Số 72 UBND KT Kính gửi Ban chỉ huy 32 xóm` trả document `718b0db1-6c8c-4da4-b6aa-5689173d219a` top 1 sau reprocess.
- Nuxt production build và Docker Compose config thành công.
- Không phát sinh runtime artifact trong git.

## Mục Tiêu Task Tiếp Theo

Hoàn thiện UX admin MVP quanh trạng thái xử lý và xác định auth scope tối thiểu sau khi API đã có guard backend.

## Ràng Buộc Không Đổi

- Không dùng cloud OCR.
- Không dùng API LLM để sửa nội dung pháp lý.
- Docker Compose first.
- MVP first.
- Backend giữ `router -> service -> repository`.
- Frontend giữ `page -> composable -> service -> API`.
- OCR pipeline local/on-prem.
- Không commit model files hoặc runtime artifacts.

## Phạm Vi Đề Xuất

### 1. Admin UX Polish

Vấn đề:
- Reprocess đã chạy được, nhưng UI admin vẫn còn ít feedback khi job chạy lâu.

Hướng xử lý:
- Thêm hiển thị thời điểm polling/cập nhật gần nhất trên document detail.
- Tách trạng thái job đang chạy nổi bật hơn trong audit list.
- Thêm confirm nhẹ trước khi bấm reprocess để tránh click nhầm OCR lại tài liệu lớn.
- Kiểm tra mobile layout cho job audit và chunks.

### 2. Auth Scope MVP

Vấn đề:
- Backend đã yêu cầu token nhưng chưa có phân quyền theo role/scope.

Hướng xử lý:
- Xác định role MVP: admin/user hoặc chỉ admin local.
- Nếu cần, thêm field role đơn giản cho user và dependency admin-only cho reprocess.
- Giữ upload/list/search trong scope đã thống nhất, không over-engineering RBAC.

## Tiêu Chí Hoàn Thành

- Reprocess UX giảm rủi ro click nhầm và hiển thị trạng thái đang xử lý rõ hơn.
- Auth scope MVP được ghi rõ trong tài liệu và code nếu cần.
- Không làm chậm workflow upload -> OCR -> search hiện tại.
