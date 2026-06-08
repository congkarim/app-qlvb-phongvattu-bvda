# UI/UX Polish Plan

Kế hoạch hoàn thiện giao diện cho `apps/web` (Nuxt 3 + PrimeVue + TailwindCSS).

## Nguyên tắc

- Không rewrite toàn bộ UI.
- Không đổi business logic, endpoint, composable/service flow.
- Giữ luồng: `page -> composable -> service -> API`.
- Không thêm UI library mới.
- Chỉ dùng PrimeVue hiện có + TailwindCSS để polish.
- Mỗi phase sửa nhóm nhỏ, có thể review độc lập.

## Hiện trạng (audit)

| Khu vực | Vấn đề |
|---------|--------|
| Layout (`app.vue`) | Nav phẳng, 10+ link tràn trên mobile; không có active state; login vẫn hiện nav |
| Spacing | Lẫn `space-y-5` / `space-y-6`; page header không thống nhất |
| Card/Table/Form | PrimeVue Card dùng trực tiếp; native `<select>` và PrimeVue Input lẫn lộn style |
| Empty/Loading/Error | Chủ yếu `<p class="text-sm text-slate-600">`; không có component chuẩn |
| Responsive | Table `min-width: 72rem` gây scroll ngang; filter grid 9 cột khó dùng trên mobile |
| Consistency | Mỗi page tự viết header, pagination bar, error block |

### Màn hình chính

| Page | Route | Ưu tiên |
|------|-------|---------|
| Login | `/login` | P1 |
| Dashboard | `/dashboard` | P2 |
| Documents list | `/documents` | P1 |
| Document detail | `/documents/[id]` | P3 |
| Upload | `/upload` | P2 |
| Contracts | `/contracts` | P2 |
| Dispatches | `/dispatches` | P2 |
| Decisions | `/decisions` | P2 |
| Procurements | `/procurements` | P2 |
| Materials catalog | `/materials-catalog` | P3 |
| Users | `/users` | P3 |
| Status | `/status` | P3 |

### Component hiện có

- `BaseDataTable`, `BaseStatusBadge`, `BaseUploadDropzone`
- `RagAnswerPanel`, `DocumentRelationsCard`, `DocumentOnboardingBanner`
- `ProcurementLineItemsPanel`

### Component cần bổ sung (theo skill)

- `AppPageHeader`, `AppPageContainer`, `AppCard`
- `AppToolbar`, `AppActionGroup`, `AppSectionTitle`
- `AppEmptyState`, `AppLoadingState`, `AppErrorState`
- `AppSelect` (chuẩn hóa native select)
- `AppNavbar` (tách khỏi `app.vue`)

---

## Phase 0 — Kế hoạch (hoàn thành)

Tạo tài liệu này và xác nhận phạm vi.

---

## Phase 1 — Foundation (P0) — Hoàn thành

**Mục tiêu:** Chuẩn hóa shell layout và component dùng chung; áp dụng thử trên 2 màn hình.

### Việc cần làm

1. Thêm utility classes trong `assets/css/main.css` (`app-select`, link nav active).
2. Tạo `components/app/*` (AppPageHeader, AppPageContainer, AppCard, AppEmptyState, AppLoadingState, AppErrorState, AppToolbar, AppSelect, AppNavbar).
3. Cập nhật `app.vue`: nền `slate-50`, ẩn nav khi `/login`, mobile menu.
4. Áp dụng lên `login.vue` và `documents/index.vue`.

### File dự kiến sửa

- `apps/web/assets/css/main.css`
- `apps/web/app.vue`
- `apps/web/components/app/*.vue` (mới)
- `apps/web/pages/login.vue`
- `apps/web/pages/documents/index.vue`
- `apps/web/components/BaseDataTable.vue` (empty/loading state)

### Tiêu chí hoàn thành

- [x] Nav responsive, login không có sidebar/top nav.
- [x] Documents list dùng App* components; error/loading/empty nhất quán.
- [x] Không đổi API call hay composable logic.

### Đã triển khai

- `components/app/`: AppPageHeader, AppPageContainer, AppCard, AppEmptyState, AppLoadingState, AppErrorState, AppToolbar, AppSectionTitle, AppSelect, AppNavbar
- `assets/css/main.css`: `.app-select`, `.app-nav-link`, `.app-table-wrap`
- `app.vue`, `login.vue`, `documents/index.vue`, `BaseDataTable.vue`

---

## Phase 2 — List pages consistency (P1)

**Mục tiêu:** Đồng bộ pattern list + filter + pagination trên các module.

### Màn hình

- `contracts.vue`, `dispatches.vue`, `decisions.vue`, `procurements.vue`

### Cải thiện

- Thay header/pagination tự viết bằng `AppPageHeader` + `AppToolbar`.
- Bọc filter trong `AppCard` với title "Bộ lọc".
- `AppSelect` thay native select.
- `AppErrorState` thay `Message` rời rạc (giữ Message cho info/warn).
- Table empty state dùng `AppEmptyState`.
- Form create/edit: label rõ, `AppSectionTitle`, grid responsive `sm:grid-cols-2`.

### File dự kiến

- `apps/web/pages/contracts.vue`
- `apps/web/pages/dispatches.vue`
- `apps/web/pages/decisions.vue`
- `apps/web/pages/procurements.vue`

---

## Phase 3 — Dashboard, Upload, Login polish (P2)

**Mục tiêu:** Cải thiện màn hình tương tác nhiều nhất.

### Dashboard (`dashboard.vue`)

- Tách section Review queue / Semantic search / RAG bằng `AppCard` + `AppSectionTitle`.
- Loading/empty/error cho review queue và search results.
- Filter grid responsive: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`.
- Search input stack vertical trên mobile.

### Upload (`upload.vue`)

- `AppPageHeader` + policy text dạng help.
- Mode toggle dùng `AppActionGroup` style.
- `AppCard` cho form và kết quả OCR.
- `AppErrorState` / success hint sau upload.

### Login (`login.vue`)

- Centered layout full-height, ẩn nav (đã xử lý ở Phase 1).
- Card shadow nhẹ, branding subtitle.

### File dự kiến

- `apps/web/pages/dashboard.vue`
- `apps/web/pages/upload.vue`
- `apps/web/components/RagAnswerPanel.vue`

---

## Phase 4 — Detail & Admin (P3)

**Mục tiêu:** Polish màn chi tiết và admin.

### Document detail (`documents/[...id].vue`)

- `AppPageHeader` với breadcrumb/back.
- Section cards cho metadata, chunks, relations.
- `DocumentOnboardingBanner` spacing.

### Admin

- `users.vue`, `status.vue`, `materials-catalog.vue`
- Dialog/form spacing; audit log table scroll.
- Admin-only nav group trong `AppNavbar`.

### File dự kiến

- `apps/web/pages/documents/[...id].vue`
- `apps/web/pages/users.vue`
- `apps/web/pages/status.vue`
- `apps/web/pages/materials-catalog.vue`
- `apps/web/components/documents/*`

---

## Phase 5 — Responsive & table UX (P2–P3)

**Mục tiêu:** Tối ưu mobile và bảng dữ liệu.

### Cải thiện

- `BaseDataTable`: `responsive-layout="scroll"`, wrapper `overflow-x-auto`.
- Pagination `AppToolbar`: nút full-width trên mobile.
- Filter panels: collapse/accordion trên mobile (optional, không đổi logic filter).
- Touch target tối thiểu 44px cho button nhỏ.
- Kiểm tra `max-w-6xl` vs `max-w-7xl` cho dashboard nhiều cột.

### File dự kiến

- `apps/web/components/BaseDataTable.vue`
- `apps/web/components/app/AppToolbar.vue`
- Các list pages đã polish ở Phase 2

---

## Visual tokens (thống nhất)

| Token | Giá trị |
|-------|---------|
| Page background | `bg-slate-50` |
| Card | `bg-white rounded-lg border border-slate-200 shadow-sm` |
| Page spacing | `space-y-6` |
| Section gap | `gap-3` / `gap-4` |
| Title | `text-2xl font-semibold tracking-tight text-slate-900` |
| Subtitle | `text-sm text-slate-600` |
| Muted text | `text-xs text-slate-500` |
| Primary link | `text-sky-700 hover:text-sky-800` |
| Container | `max-w-6xl mx-auto px-4 sm:px-6` |

---

## Thứ tự ưu tiên tổng hợp

1. **P0** — Phase 1 Foundation (layout + App* components)
2. **P1** — Documents list + module list pages (Phase 2)
3. **P2** — Dashboard, Upload (Phase 3) + table responsive (Phase 5)
4. **P3** — Detail, Admin (Phase 4)

---

## Kiểm tra sau mỗi phase

- [ ] `npm run build` trong `apps/web` thành công
- [ ] Không đổi composable/service/API
- [ ] Mobile viewport 375px không vỡ layout nav
- [ ] Loading/error/empty hiển thị đúng trên ít nhất 1 list page

---

## Ghi chú

- Không thêm logout/user menu trong scope polish trừ khi có yêu cầu riêng (tránh đụng auth flow).
- PrimeVue `Select` component chưa register — Phase 1 dùng `AppSelect` (native styled) để tránh đổi plugin.
- Có thể migrate sang PrimeVue Select sau khi pattern ổn định.
