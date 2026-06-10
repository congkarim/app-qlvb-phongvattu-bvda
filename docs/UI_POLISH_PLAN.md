# UI/UX Polish Plan

Kế hoạch hoàn thiện giao diện cho `apps/web` (Nuxt 3 + PrimeVue + TailwindCSS).

## Nguyên tắc

- Không rewrite toàn bộ UI.
- Không đổi business logic, endpoint, composable/service flow.
- Giữ luồng: `page -> composable -> service -> API`.
- Không thêm UI library mới.
- Chỉ dùng PrimeVue hiện có + TailwindCSS để polish.
- Mỗi phase sửa nhóm nhỏ, có thể review độc lập.

---

## Phase 0 — Kế hoạch (hoàn thành)

Tạo tài liệu này và xác nhận phạm vi.

---

## Phase 1 — Foundation (hoàn thành)

- `components/app/*`, `AppNavbar`, `login.vue`, `documents/index.vue`, `BaseDataTable` empty state.

---

## Phase 2 — List pages consistency (hoàn thành — Phase 19)

- `contracts.vue`, `dispatches.vue`, `decisions.vue`, `procurements.vue`
- Pattern: `AppPageContainer` → `AppPageHeader` → `AppCard` → `AppSelect` → `AppToolbar` → table.

---

## Phase 3 — Dashboard, Upload (hoàn thành — Phase 19)

- `dashboard.vue`: `AppPageContainer`, `AppPageHeader`, `AppCard` sections, widget tồn thấp.
- `upload.vue`: `AppActionGroup` mode toggle, `AppPageHeader`, `AppCard`.

---

## Phase 4 — Detail & Admin (một phần — Phase 19)

- [x] `users.vue`, `status.vue`, `materials-catalog.vue`
- [ ] `documents/[...id].vue` — backlog (header phức tạp, chưa polish)

---

## Phase 5 — Responsive & table UX (hoàn thành cơ bản — Phase 19)

- `app-table-wrap` trên list pages đã polish.
- `AppToolbar` dùng thống nhất.
- Touch target `AppActionGroup` ≥ 44px.

---

## Phase 6 — Inventory UI (hoàn thành — Phase 19)

**Prerequisite:** Phase 2 polish `procurements.vue` + `materials-catalog.vue`.

### Component mới

- `AppActionGroup` — toggle loại phiếu nhập/xuất
- `StockLevelBadge` — badge tồn đủ/thấp/hết
- `MaterialsCatalogAutocomplete` — tái sử dụng autocomplete catalog

### Màn hình

- `/stock-movements` — list + dialog phiếu
- `/materials-catalog` — cột tồn, min level, filter `below_min`
- Dashboard — card vật tư tồn thấp
- `ProcurementLineItemsPanel` — nhập kho từ hồ sơ acceptance
- `AppNavbar` — link **Tồn kho**

---

## Kiểm tra sau mỗi phase

- [x] `npm run build` trong `apps/web` thành công
- [x] Không đổi composable/service/API (chỉ thêm inventory API mới)
- [x] Mobile viewport 375px — nav + list pages

---

## Ghi chú

- PrimeVue `Select` chưa register — dùng `AppSelect` (native styled).
- Logout/user menu ngoài scope polish.
