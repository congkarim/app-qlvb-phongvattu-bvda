# Kế Hoạch Task Tiếp Theo

Cập nhật lần cuối: 2026-06-10

Phase trước: Phase 18 hoàn thành ngày 2026-06-08.

Phase hiện tại: **Phase 19 hoàn thành** — Inventory/tồn kho MVP + UI polish Phases 2–6.

Mục tiêu tiếp theo: Phase 20+ (workflow phê duyệt, LLM ops) — chưa mở. Xem `ROADMAP.md`.

## Regression sau Phase 19

```bash
docker compose exec -T api python -m app.scripts.smoke_inventory
docker compose exec -T api python -m app.scripts.smoke_procurement_line_items
docker compose exec -T api python -m app.scripts.smoke_procurement_api
docker compose exec -T api python -m app.scripts.smoke_search_module_filters
docker compose exec -T api python -m app.scripts.smoke_module_onboarding
docker compose exec -T api python -m app.scripts.smoke_rag_answer
docker compose exec -T api python -m app.scripts.smoke_relation_suggestions
docker compose exec -T api python -m app.scripts.smoke_health_checks
WEB_MEMORY_LIMIT=4g docker compose run --rm --no-deps -e NODE_OPTIONS=--max-old-space-size=3072 web npm run build
```
