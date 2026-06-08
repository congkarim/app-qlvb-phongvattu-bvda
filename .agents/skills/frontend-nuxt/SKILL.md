---
name: frontend-nuxt
description: Xây dựng frontend Nuxt 3 cho hệ thống quản lý văn bản OCR và semantic search.
---

# Frontend Nuxt Skill

## Responsibilities

- Xây dựng UI quản lý văn bản, upload, preview, metadata và search.
- Tổ chức code Nuxt 3 theo page, composable, service và API client.
- Tạo component nhỏ, dễ tái sử dụng, phù hợp PrimeVue và TailwindCSS.
- Quản lý state bằng Pinia khi state được dùng chéo nhiều màn hình.

## Rules

- Không gọi API trực tiếp trong component.
- Luồng bắt buộc: `page -> composable -> service -> API`.
- Component phải nhỏ, rõ trách nhiệm và tái sử dụng được.
- Không nhồi business workflow vào UI component.
- Không tự đổi UI stack.
- Ưu tiên màn hình MVP dễ dùng, tải nhanh, ít trạng thái mơ hồ.
- Form phải có validation, loading state và error state.

## Architecture

```text
page -> composable -> service -> API
```

Khuyến nghị cấu trúc:

```text
pages/
components/
composables/
services/
stores/
types/
utils/
```

## Stack

- Nuxt 3
- TypeScript
- PrimeVue
- TailwindCSS
- Pinia

## Modules

- Auth pages and session state.
- Document list, filters, detail and preview.
- Upload flow and OCR status tracking.
- Contract, dispatch and decision views.
- Semantic search page with metadata filters.
- Audit log viewer for admin roles.

## Suggested Components

- `BaseDataTable`
- `BaseFilterPanel`
- `BaseUploadDropzone`
- `BaseStatusBadge`
- `DocumentPreviewDrawer`
- `MetadataForm`

## Coding Conventions

- Component props và emits phải typed.
- API service trả typed response, không trả `any` khi có thể tránh.
- Composable quản lý loading, error, pagination và filter state.
- Store Pinia chỉ dùng cho session, user context, shared filters hoặc state dùng lại nhiều nơi.
- Tách type nghiệp vụ vào `types/`.
- Component table/filter/upload phải generic đủ dùng lại cho documents, contracts, dispatches và decisions.
- Không hardcode endpoint trong component.
- Không đặt logic mapping API response phức tạp trong template.

## UI/UX Polish Rules

- App đã chạy được thì không rewrite toàn bộ UI.
- Chỉ cải thiện từng màn hình/component nhỏ.
- Không phá flow `page -> composable -> service -> API`.
- Ưu tiên giữ PrimeVue component hiện có.
- TailwindCSS dùng để polish layout, spacing, responsive, state.
- Không đổi stack UI.
- Không thêm thư viện UI mới nếu chưa có lý do rõ.

## Visual Standard

- Giao diện sạch, hiện đại, chuyên nghiệp, phù hợp hệ thống bệnh viện/quản lý văn bản.
- Mobile-first.
- Nền tổng thể dùng màu nhẹ: `surface-50`, `slate-50` hoặc tương đương.
- Nội dung chính đặt trong container có giới hạn chiều rộng.
- Card trắng, bo góc vừa, shadow nhẹ, border mảnh.
- Khoảng cách thống nhất: `gap-2`, `gap-3`, `gap-4`, `gap-6`.
- Không nhồi quá nhiều thông tin vào một màn hình.
- Table phải có empty state, loading state, error state.
- Form phải có label rõ, help text khi cần, validation message dễ hiểu.
- Button action chính/phụ/nguy hiểm phải phân cấp rõ.
- Icon button phải có tooltip hoặc aria-label.

## Reusable UI Components

Bổ sung hoặc chuẩn hóa các component:

- `AppPageHeader`
- `AppPageContainer`
- `AppCard`
- `AppToolbar`
- `AppEmptyState`
- `AppLoadingState`
- `AppErrorState`
- `AppActionGroup`
- `AppSectionTitle`

## UI Audit Workflow

Khi được yêu cầu polish UI:

1. Đọc project hiện tại.
2. Xác định các page chính.
3. Không sửa code ngay.
4. Tạo `docs/UI_POLISH_PLAN.md`.
5. Trong plan phải có:
   - màn hình cần sửa
   - vấn đề hiện tại
   - hướng cải thiện
   - file dự kiến sửa
   - mức ưu tiên
6. Sau đó mới sửa từng nhóm nhỏ.
7. Mỗi lần sửa phải đảm bảo:
   - không đổi business logic
   - không đổi API flow
   - không đổi endpoint
   - không phá TypeScript
   - chạy lint/typecheck nếu project có script
