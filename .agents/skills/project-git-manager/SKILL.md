---
name: project-git-manager
description: Quản lý tiến độ dự án bằng git, cập nhật tài liệu trạng thái và ghi nhận thay đổi repo sau mỗi task hoàn thành.
---

# Project Git Manager Skill

## Responsibilities

- Quản lý vòng đời task bằng git trong repo local.
- Kiểm tra trạng thái repo trước khi sửa code.
- Cập nhật tài liệu tiến độ sau khi hoàn thành task.
- Commit thay đổi liên quan tới task khi đã kiểm tra xong.
- Giữ lịch sử git rõ ràng, nhỏ gọn và truy vết được.

## Rules

- Không dùng cloud service hoặc CI/CD mới nếu chưa có yêu cầu rõ ràng.
- Không đổi stack kỹ thuật của dự án.
- Không commit file sinh ra từ dev server, cache, upload, `.env`, `node_modules`, `.nuxt`, `.output`, `dist`.
- Không revert thay đổi không do mình tạo.
- Không gom thay đổi không liên quan vào cùng một commit.
- Không commit khi test/check quan trọng đang fail mà chưa ghi rõ lý do.
- Nếu repo chưa có `.git` và người dùng yêu cầu quản lý bằng git, có thể bootstrap bằng `git init` rồi tạo commit đầu tiên cho trạng thái hiện tại.

## Start Of Task

1. Chạy:

```bash
git status --short
git branch --show-current
```

2. Nếu chưa phải git repo:
   - Kiểm tra `.gitignore`.
   - Chạy `git init` khi task yêu cầu quản lý repo bằng git.
   - Không add file bị ignore hoặc artifact runtime.

3. Đọc tài liệu trạng thái liên quan:
   - `PROJECT_STATUS.md`
   - `TASK_NEXT.md`
   - `README.md` nếu task thay đổi cách chạy, test hoặc workflow.

4. Ghi nhận thay đổi sẵn có của user và chỉ chạm vào file cần thiết cho task.

## During Task

- Làm thay đổi nhỏ, theo đúng skill kỹ thuật tương ứng.
- Sau mỗi nhóm thay đổi lớn, kiểm tra `git diff --check`.
- Nếu phát hiện file sinh tự động ngoài `.gitignore`, cập nhật `.gitignore` thay vì commit artifact.
- Với thay đổi backend/frontend/database/OCR/search, giữ đúng kiến trúc:

```text
backend: router -> service -> repository
frontend: page -> composable -> service -> API
```

## Completion Workflow

Khi task hoàn thành:

1. Chạy kiểm tra phù hợp với phạm vi thay đổi:
   - Lint/typecheck/test nếu project có script sẵn.
   - `docker compose config` khi thay đổi Docker Compose.
   - Manual curl/browser verification khi task là workflow MVP.

2. Cập nhật tài liệu repo:
   - `PROJECT_STATUS.md`: trạng thái hiện tại, hạng mục đã làm, giới hạn còn lại, kiểm tra đã chạy.
   - `TASK_NEXT.md`: chỉ giữ checklist phase đang làm; cập nhật trạng thái mục tiêu hoặc thay bằng phase kế tiếp khi phase hiện tại hoàn thành. Lịch sử phase ghi trong `PROJECT_STATUS.md`.
   - `README.md`: chỉ cập nhật khi cách chạy/test/workflow thay đổi.

3. Kiểm tra diff:

```bash
git status --short
git diff --check
git diff --stat
```

4. Stage có chọn lọc:

```bash
git add <related-files>
```

5. Commit sau khi task đã hoàn tất:

```bash
git commit -m "<type>: <short Vietnamese or English summary>"
```

Ưu tiên type:
- `feat`: thêm chức năng hoặc skill mới.
- `fix`: sửa lỗi.
- `docs`: chỉ sửa tài liệu.
- `chore`: cấu hình, quản lý repo, cleanup không ảnh hưởng runtime.
- `test`: thêm hoặc sửa test.

## Commit Message

- Ngắn, cụ thể, mô tả kết quả đã hoàn thành.
- Không nhắc tới tool/agent trừ khi task thật sự là về agent system.
- Ví dụ:

```text
feat: add project git management skill
docs: update MVP workflow status
fix: handle document detail polling cleanup
```

## Final Response

Kết thúc task bằng thông tin ngắn gọn:

- File chính đã thay đổi.
- Kiểm tra đã chạy và kết quả.
- Commit hash nếu đã commit.
- Nếu chưa commit được, nêu lý do cụ thể.
