from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy.orm import Session

from app.models.procurement_line_item import ProcurementLineItem
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.procurement_line_item_repository import ProcurementLineItemRepository
from app.services.materials_catalog_service import MaterialsCatalogNotFoundError, MaterialsCatalogService
from app.services.procurement_service import ProcurementNotFoundError


class ProcurementLineItemNotFoundError(ValueError):
    pass


class ProcurementLineItemOperationError(ValueError):
    pass


class ProcurementLineItemAlreadyExistsError(ValueError):
    pass


class ProcurementLineItemService:
    def __init__(self, db: Session):
        self.db = db
        self.line_items = ProcurementLineItemRepository(db)
        self.audit_logs = AuditLogRepository(db)
        self.materials_catalog = MaterialsCatalogService(db)

    def list_line_items(self, procurement_id: str) -> dict[str, Any]:
        self._ensure_procurement(procurement_id)
        items = self.line_items.list_by_procurement_id(procurement_id)
        return self._list_response(items, procurement_id=procurement_id)

    def create_line_item(
        self,
        *,
        procurement_id: str,
        values: dict[str, Any],
        actor: User,
    ) -> dict[str, Any]:
        self._ensure_procurement(procurement_id)
        payload = self._clean_create_values(values)
        catalog_item_id = payload.get("catalog_item_id")
        self.materials_catalog.ensure_catalog_reference(catalog_item_id)
        line_number = payload.pop("line_number", None)
        if line_number is None:
            line_number = self.line_items.get_max_line_number(procurement_id) + 1
        else:
            self._ensure_unique_line_number(procurement_id, line_number)

        explicit_amount = payload.pop("explicit_amount", None)
        quantity = payload["quantity"]
        unit_price = payload.get("unit_price")
        payload["amount"] = self._compute_amount(
            quantity=quantity,
            unit_price=unit_price,
            explicit_amount=explicit_amount,
        )

        item = self.line_items.create(
            procurement_id=procurement_id,
            line_number=line_number,
            **payload,
        )
        self.audit_logs.create(
            action="procurement_line_item.created",
            entity_type="procurement_line_item",
            entity_id=item.id,
            actor_user_id=actor.id,
            metadata={
                "procurement_id": procurement_id,
                "line_number": item.line_number,
                "item_name": item.item_name,
            },
        )
        self.db.commit()
        self.db.refresh(item)
        return self._read(item)

    def update_line_item(
        self,
        *,
        line_item_id: str,
        values: dict[str, Any],
        actor: User,
    ) -> dict[str, Any]:
        item = self._get_line_item(line_item_id)
        old_values = self._audit_snapshot(item)
        cleaned = self._clean_update_values(values)

        if "catalog_item_id" in values:
            self.materials_catalog.ensure_catalog_reference(cleaned.get("catalog_item_id"))

        if "line_number" in cleaned and cleaned["line_number"] != item.line_number:
            self._ensure_unique_line_number(item.procurement_id, cleaned["line_number"], exclude_id=item.id)

        quantity = cleaned.get("quantity", item.quantity)
        if "unit_price" in values:
            unit_price = cleaned.get("unit_price")
        else:
            unit_price = item.unit_price

        if unit_price is not None:
            cleaned["amount"] = self._compute_amount(
                quantity=quantity,
                unit_price=unit_price,
                explicit_amount=None,
            )
        elif "amount" in values:
            cleaned["amount"] = cleaned.pop("explicit_amount", None)

        update_payload = {key: value for key, value in cleaned.items() if key != "explicit_amount"}
        item = self.line_items.update(item, **update_payload)
        self.audit_logs.create(
            action="procurement_line_item.updated",
            entity_type="procurement_line_item",
            entity_id=item.id,
            actor_user_id=actor.id,
            metadata={"procurement_id": item.procurement_id, "old": old_values, "new": self._audit_snapshot(item)},
        )
        self.db.commit()
        self.db.refresh(item)
        return self._read(item)

    def delete_line_item(self, *, line_item_id: str, actor: User) -> dict[str, Any]:
        item = self._get_line_item(line_item_id)
        item = self.line_items.soft_delete(item)
        self.audit_logs.create(
            action="procurement_line_item.deleted",
            entity_type="procurement_line_item",
            entity_id=item.id,
            actor_user_id=actor.id,
            metadata={
                "procurement_id": item.procurement_id,
                "line_number": item.line_number,
                "item_name": item.item_name,
            },
        )
        self.db.commit()
        self.db.refresh(item)
        return self._read(item)

    def _ensure_procurement(self, procurement_id: str) -> None:
        if self.line_items.get_procurement(procurement_id) is None:
            raise ProcurementNotFoundError("Procurement metadata not found")

    def _get_line_item(self, line_item_id: str) -> ProcurementLineItem:
        item = self.line_items.get_by_id(line_item_id)
        if item is None:
            raise ProcurementLineItemNotFoundError("Procurement line item not found")
        return item

    def _ensure_unique_line_number(
        self,
        procurement_id: str,
        line_number: int,
        *,
        exclude_id: str | None = None,
    ) -> None:
        existing = self.line_items.get_by_procurement_and_line_number(procurement_id, line_number)
        if existing is not None and existing.id != exclude_id:
            raise ProcurementLineItemAlreadyExistsError(
                f"Line number {line_number} already exists for this procurement"
            )

    def _clean_create_values(self, values: dict[str, Any]) -> dict[str, Any]:
        item_name = self._normalize_required(values.get("item_name"), "item_name")
        quantity = self._normalize_quantity(values.get("quantity", Decimal("1")))
        unit_price = self._normalize_optional_decimal(values.get("unit_price"), "unit_price")
        explicit_amount = self._normalize_optional_decimal(values.get("amount"), "amount")
        line_number = values.get("line_number")
        if line_number is not None and int(line_number) < 1:
            raise ProcurementLineItemOperationError("line_number must be >= 1")
        return {
            "line_number": int(line_number) if line_number is not None else None,
            "item_name": item_name,
            "item_code": self._normalize_text(values.get("item_code")),
            "unit": self._normalize_text(values.get("unit")),
            "quantity": quantity,
            "unit_price": unit_price,
            "explicit_amount": explicit_amount,
            "catalog_item_id": self._normalize_text(values.get("catalog_item_id")),
            "notes": self._normalize_text(values.get("notes")),
        }

    def _clean_update_values(self, values: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        if "line_number" in values:
            line_number = values.get("line_number")
            if line_number is not None and int(line_number) < 1:
                raise ProcurementLineItemOperationError("line_number must be >= 1")
            cleaned["line_number"] = int(line_number) if line_number is not None else None
        if "item_name" in values:
            cleaned["item_name"] = self._normalize_required(values.get("item_name"), "item_name")
        if "item_code" in values:
            cleaned["item_code"] = self._normalize_text(values.get("item_code"))
        if "unit" in values:
            cleaned["unit"] = self._normalize_text(values.get("unit"))
        if "quantity" in values:
            cleaned["quantity"] = self._normalize_quantity(values.get("quantity"))
        if "unit_price" in values:
            cleaned["unit_price"] = self._normalize_optional_decimal(values.get("unit_price"), "unit_price")
        if "amount" in values:
            cleaned["explicit_amount"] = self._normalize_optional_decimal(values.get("amount"), "amount")
        if "catalog_item_id" in values:
            cleaned["catalog_item_id"] = self._normalize_text(values.get("catalog_item_id"))
        if "notes" in values:
            cleaned["notes"] = self._normalize_text(values.get("notes"))
        return cleaned

    def _compute_amount(
        self,
        *,
        quantity: Decimal,
        unit_price: Decimal | None,
        explicit_amount: Decimal | None,
    ) -> Decimal | None:
        if unit_price is not None:
            return (quantity * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return explicit_amount

    def _list_response(self, items: list[ProcurementLineItem], *, procurement_id: str) -> dict[str, Any]:
        lines_total = self.line_items.sum_amount_by_procurement_id(procurement_id)
        return {
            "items": [self._read(item) for item in items],
            "total": len(items),
            "lines_total_amount": lines_total,
        }

    def _read(self, item: ProcurementLineItem) -> dict[str, Any]:
        return {
            "id": item.id,
            "procurement_id": item.procurement_id,
            "line_number": item.line_number,
            "item_name": item.item_name,
            "item_code": item.item_code,
            "unit": item.unit,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "amount": item.amount,
            "catalog_item_id": item.catalog_item_id,
            "notes": item.notes,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }

    def _audit_snapshot(self, item: ProcurementLineItem) -> dict[str, Any]:
        return {
            "line_number": item.line_number,
            "item_name": item.item_name,
            "item_code": item.item_code,
            "quantity": str(item.quantity),
            "unit_price": str(item.unit_price) if item.unit_price is not None else None,
            "amount": str(item.amount) if item.amount is not None else None,
        }

    def _normalize_quantity(self, value: Any) -> Decimal:
        if value is None:
            raise ProcurementLineItemOperationError("quantity is required")
        quantity = Decimal(str(value))
        if quantity < 0:
            raise ProcurementLineItemOperationError("quantity cannot be negative")
        return quantity

    def _normalize_optional_decimal(self, value: Any, field_name: str) -> Decimal | None:
        if value is None:
            return None
        decimal_value = Decimal(str(value))
        if decimal_value < 0:
            raise ProcurementLineItemOperationError(f"{field_name} cannot be negative")
        return decimal_value

    def _normalize_text(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _normalize_required(self, value: Any, field_name: str) -> str:
        normalized = self._normalize_text(value)
        if normalized is None:
            raise ProcurementLineItemOperationError(f"{field_name} is required")
        return normalized
