# Task Đã Hoàn Thành: Hoàn Thiện Workflow MVP Trên Web UI

Trạng thái: đã triển khai.

Ngày hoàn thành: 2026-05-28

## Cập Nhật Mới Nhất

Task bổ sung đã hoàn thành:
- Tạo skill `.agents/skills/project-git-manager/SKILL.md`.
- Cập nhật `AGENTS.md` để nhắc dùng skill này khi hoàn thành task.
- Cập nhật `README.md` và `PROJECT_STATUS.md` để ghi nhận skill quản lý repo bằng git.

Kỳ vọng từ các task sau:
- Đầu task kiểm tra trạng thái git.
- Cuối task cập nhật tài liệu trạng thái phù hợp.
- Commit có chọn lọc các thay đổi liên quan sau khi kiểm tra xong.

## Mục Tiêu

Biến skeleton hiện tại thành một workflow MVP có thể dùng được từ frontend Nuxt.

Workflow mục tiêu:

```text
Mở web UI
-> upload văn bản
-> thấy kết quả upload
-> mở trang chi tiết văn bản
-> theo dõi OCR status chuyển sang searchable
-> chạy semantic search
-> mở lại văn bản nguồn từ kết quả search
```

Chưa thay OCR skeleton hoặc fake embedding trong bước này. Mục tiêu là làm cho pipeline end-to-end hiện tại dùng được qua trình duyệt.

## Phạm Vi

Trong phạm vi:
- Cải thiện upload flow trên frontend.
- Cải thiện hiển thị trạng thái ở document detail.
- Thêm polling OCR status ở document detail.
- Cải thiện UX semantic search trên dashboard.
- Chỉ thêm backend support tối thiểu nếu UI workflow thật sự cần.
- Cập nhật README với cách test bằng web.

Ngoài phạm vi:
- OCR thật bằng PaddleOCR.
- Local embedding model thật.
- Auth/phân quyền nâng cao.
- UI polish production-level.
- CI/CD.
- Kubernetes.
- Cloud service.
- Microservice mới.

## Điểm Bắt Đầu Hiện Tại

Backend đã có:
- `GET /health`
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_id}`
- `POST /api/v1/search/semantic`

Worker đã có:
- Poll OCR job pending.
- Giả lập OCR.
- Tạo page/chunk.
- Fake embedding.
- Upsert Qdrant.
- Chuyển document sang `searchable`.

Frontend đã có:
- `/dashboard`
- `/documents`
- `/upload`
- `/documents/[id]`
- `useDocuments`
- `useSemanticSearch`
- API service layer.

## Task Chi Tiết

### 1. Upload Page Workflow

Cải thiện `/upload` để giống workflow người vận hành thực tế.

Yêu cầu:
- Hiển thị tên file, dung lượng và content type đã chọn.
- Disable nút upload khi chưa chọn file.
- Hiển thị loading khi đang upload.
- Hiển thị lỗi rõ ràng nếu upload fail.
- Sau khi upload thành công, hiển thị document ID và OCR job status.
- Có action chính để mở document detail.
- Ưu tiên tự điều hướng sang `/documents/{id}` sau khi upload thành công, trừ khi làm mất feedback trạng thái.

Tiêu chí hoàn thành:
- Người dùng upload được file `.txt` từ trình duyệt.
- Upload API chỉ được gọi qua `composable -> service -> API`.
- Không gọi API trực tiếp trong component.
- Người dùng mở được document detail mà không cần copy ID thủ công.

Test thủ công:

```text
Mở http://localhost:3000/upload
Chọn file .txt
Bấm Upload
Xác nhận có thể mở document detail
```

### 2. Document Detail OCR Status

Cải thiện `/documents/[id]` để hiển thị rõ trạng thái xử lý.

Yêu cầu:
- Hiển thị metadata văn bản:
  - title
  - original filename
  - document type
  - status
  - created_at
  - updated_at
- Hiển thị OCR job status mới nhất.
- Hiển thị OCR page text khi có.
- Hiển thị chunks khi có.
- Nếu document status chưa phải `searchable`, polling detail endpoint mỗi vài giây.
- Dừng polling khi status là `searchable` hoặc `failed`.
- Không để polling tiếp tục sau khi rời trang.

Tiêu chí hoàn thành:
- Ngay sau upload, detail page hiển thị pending/running status.
- Sau khi worker hoàn tất, status tự đổi sang `searchable` mà không cần refresh tay.
- OCR text và chunks xuất hiện sau khi xử lý.

Test thủ công:

```text
Upload sample .txt
Mở document detail ngay
Quan sát status chuyển sang searchable
Xác nhận OCR text và chunks được render
```

### 3. Documents List

Cải thiện `/documents` để dễ scan dữ liệu MVP.

Yêu cầu:
- Hiển thị loading state.
- Hiển thị empty state khi chưa có document.
- Hiển thị status badge.
- Có action refresh.
- Link title sang detail page.
- Giữ `BaseDataTable` đủ reusable.

Tiêu chí hoàn thành:
- Người dùng tìm thấy document vừa upload.
- Refresh không reload toàn bộ page.
- Table vẫn đủ generic để tái sử dụng.

Test thủ công:

```text
Mở http://localhost:3000/documents
Xác nhận document đã upload xuất hiện
Click title document
Xác nhận mở detail
```

### 4. Dashboard Semantic Search

Cải thiện search behavior ở `/dashboard`.

Yêu cầu:
- Search input là bắt buộc.
- Hiển thị loading state.
- Hiển thị empty state khi không có kết quả.
- Hiển thị title, score, preview text và page range nếu có.
- Mỗi result link về document detail.
- Hiển thị lỗi rõ ràng nếu API/Qdrant fail.

Tiêu chí hoàn thành:
- Người dùng search được từ trình duyệt sau khi upload xử lý xong.
- Search result link về document detail.
- Empty/error state dễ hiểu.

Test thủ công:

```text
Mở http://localhost:3000/dashboard
Search "quản lý vật tư"
Xác nhận có ít nhất một kết quả sau khi upload sample
Click title kết quả
Xác nhận mở document detail
```

### 5. Cập Nhật README

Cập nhật README sau khi UI workflow chạy ổn.

Thêm:
- Cách chạy full stack.
- Cách test upload bằng browser.
- Cách test search bằng browser.
- Cách xem worker logs.
- Giới hạn hiện tại của MVP.

Tiêu chí hoàn thành:
- Developer có thể clone/chạy theo README để test MVP.
- README phân biệt rõ test bằng browser và test bằng `curl`.

## Thứ Tự Triển Khai Đề Xuất

1. Xác nhận stack hiện tại chạy được:

```bash
docker compose up --build
```

2. Sửa workflow `/upload`.
3. Thêm polling/status cho `/documents/[id]`.
4. Cải thiện state của `/documents`.
5. Cải thiện state của `/dashboard`.
6. Cập nhật README.
7. Chạy manual browser/curl verification.

## Lệnh Kiểm Tra

API health:

```bash
curl http://localhost:8000/health
```

List documents:

```bash
curl http://localhost:8000/api/v1/documents
```

Semantic search:

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query":"quản lý vật tư","limit":5}'
```

Worker logs:

```bash
docker compose logs -f worker
```

Frontend:

```text
http://localhost:3000
```

## Định Nghĩa Hoàn Thành

Task này hoàn thành khi:
- Người dùng có thể hoàn tất upload -> processing -> searchable -> search -> mở document nguồn từ browser.
- Không có API call trực tiếp trong frontend components/pages.
- Backend vẫn giữ kiến trúc `router -> service -> repository`.
- Frontend vẫn giữ kiến trúc `page -> composable -> service -> API`.
- README phản ánh đúng workflow đã test.
- Chưa thêm OCR thật hoặc embedding thật.

## Ghi Chú Sau Khi Hoàn Thành

Các phần đã triển khai:
- Upload page hiển thị file name, file size, content type, loading/error state.
- Upload thành công tự điều hướng sang document detail.
- Document detail hiển thị metadata, OCR job, OCR text, chunks.
- Document detail tự polling trạng thái cho tới khi `searchable` hoặc `failed`.
- Documents list có refresh, empty state, loading state và link sang detail.
- Dashboard search có validation, loading, empty, error state và link sang document nguồn.
- README đã bổ sung browser workflow test.

Task tiếp theo nên được tạo riêng, ưu tiên một trong hai hướng:
- OCR thật bằng PaddleOCR/OpenCV cho PDF/image.
- Auth/seed admin/route guard nếu cần bảo vệ hệ thống trước.
