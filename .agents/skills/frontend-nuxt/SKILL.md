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
