from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.stock_movement import StockMovement
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.materials_catalog_repository import MaterialsCatalogRepository
from app.repositories.procurement_repository import ProcurementRepository
from app.repositories.stock_balance_repository import StockBalanceRepository
from app.repositories.stock_movement_repository import StockMovementRepository


class StockMovementNotFoundError(ValueError):
    pass


class StockMovementOperationError(ValueError):
    pass


class StockMovementService:
    def __init__(self, db: Session):
        self.db = db
        self.movements = StockMovementRepository(db)
        self.balances = StockBalanceRepository(db)
        self.catalog = MaterialsCatalogRepository(db)
        self.procurements = ProcurementRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def list_movements(
        self,
        *,
        movement_type: str | None,
        catalog_item_id: str | None,
        query: str | None,
        reference_number: str | None,
        movement_date_from: date | None,
        movement_date_to: date | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        items = self.movements.list_movements(
            movement_type=self._normalize_movement_type(movement_type),
            catalog_item_id=catalog_item_id,
            query=self._normalize_text(query),
            reference_number=self._normalize_text(reference_number),
            movement_date_from=movement_date_from,
            movement_date_to=movement_date_to,
            limit=limit,
            offset=offset,
        )
        total = self.movements.count_movements(
            movement_type=self._normalize_movement_type(movement_type),
            catalog_item_id=catalog_item_id,
            query=self._normalize_text(query),
            reference_number=self._normalize_text(reference_number),
            movement_date_from=movement_date_from,
            movement_date_to=movement_date_to,
        )
        return [self._read(item) for item in items], total

    def get_movement(self, movement_id: str) -> dict[str, Any]:
        return self._read(self._get_movement(movement_id))

    def get_balance(self, catalog_item_id: str) -> dict[str, Any]:
        item = self.catalog.get_by_id(catalog_item_id)
        if item is None:
            raise StockMovementOperationError("Materials catalog item not found")
        quantity = self.balances.get_balance_for_catalog(catalog_item_id)
        return self._balance_read(item, quantity)

    def list_low_stock(self, *, limit: int) -> tuple[list[dict[str, Any]], int]:
        rows = self.balances.list_low_stock(limit=limit)
        total = self.balances.count_low_stock()
        items = [self._balance_read(catalog_item, balance.quantity) for catalog_item, balance in rows]
        return items, total

    def create_movement(self, *, values: dict[str, Any], actor: User) -> dict[str, Any]:
        payload = self._clean_create_values(values)
        catalog_item = self.catalog.get_by_id(payload["catalog_item_id"])
        if catalog_item is None:
            raise StockMovementOperationError("Materials catalog item not found")
        if not catalog_item.is_active:
            raise StockMovementOperationError("Materials catalog item is not active")

        if payload.get("procurement_id"):
            procurement = self.procurements.get_by_id(payload["procurement_id"])
            if procurement is None:
                raise StockMovementOperationError("Procurement record not found")

        balance = self.balances.get_or_create(payload["catalog_item_id"])
        quantity = payload["quantity"]
        if payload["movement_type"] == "in":
            new_quantity = balance.quantity + quantity
        else:
            new_quantity = balance.quantity - quantity

        movement = self.movements.create(
            catalog_item_id=payload["catalog_item_id"],
            movement_type=payload["movement_type"],
            quantity=quantity,
            movement_date=payload["movement_date"],
            notes=payload.get("notes"),
            reference_number=payload.get("reference_number"),
            procurement_id=payload.get("procurement_id"),
            balance_after=new_quantity,
            created_by_user_id=actor.id,
        )
        self.balances.update_quantity(balance, new_quantity)
        self.audit_logs.create(
            action="stock_movement.created",
            entity_type="stock_movement",
            entity_id=movement.id,
            actor_user_id=actor.id,
            metadata={
                "movement_type": movement.movement_type,
                "catalog_item_id": movement.catalog_item_id,
                "quantity": str(movement.quantity),
                "balance_after": str(movement.balance_after),
            },
        )
        self.db.commit()
        refreshed = self._get_movement(movement.id)
        return self._read(refreshed)

    def delete_movement(self, *, movement_id: str, actor: User) -> dict[str, Any]:
        movement = self._get_movement(movement_id)
        snapshot = self._read(movement)
        balance = self.balances.get_or_create(movement.catalog_item_id)
        if movement.movement_type == "in":
            new_quantity = balance.quantity - movement.quantity
        else:
            new_quantity = balance.quantity + movement.quantity
        self.balances.update_quantity(balance, new_quantity)
        self.movements.soft_delete(movement)
        self.audit_logs.create(
            action="stock_movement.deleted",
            entity_type="stock_movement",
            entity_id=movement.id,
            actor_user_id=actor.id,
            metadata={"movement_type": movement.movement_type, "catalog_item_id": movement.catalog_item_id},
        )
        self.db.commit()
        return snapshot

    def _get_movement(self, movement_id: str) -> StockMovement:
        movement = self.movements.get_by_id(movement_id)
        if movement is None:
            raise StockMovementNotFoundError("Stock movement not found")
        return movement

    def _read(self, movement: StockMovement) -> dict[str, Any]:
        catalog_item = movement.catalog_item
        return {
            "id": movement.id,
            "catalog_item_id": movement.catalog_item_id,
            "catalog_item_code": catalog_item.code if catalog_item else None,
            "catalog_item_name": catalog_item.name if catalog_item else "",
            "catalog_item_unit": catalog_item.default_unit if catalog_item else None,
            "movement_type": movement.movement_type,
            "quantity": movement.quantity,
            "movement_date": movement.movement_date,
            "notes": movement.notes,
            "reference_number": movement.reference_number,
            "procurement_id": movement.procurement_id,
            "balance_after": movement.balance_after,
            "created_by_user_id": movement.created_by_user_id,
            "created_by_email": movement.created_by.email if movement.created_by else None,
            "created_at": movement.created_at,
            "updated_at": movement.updated_at,
        }

    def _balance_read(self, catalog_item, quantity: Decimal) -> dict[str, Any]:
        min_level = catalog_item.min_stock_level
        is_below = min_level is not None and quantity <= min_level
        return {
            "catalog_item_id": catalog_item.id,
            "catalog_item_code": catalog_item.code,
            "catalog_item_name": catalog_item.name,
            "catalog_item_unit": catalog_item.default_unit,
            "quantity": quantity,
            "min_stock_level": min_level,
            "is_below_min": is_below,
        }

    def _clean_create_values(self, values: dict[str, Any]) -> dict[str, Any]:
        movement_type = self._normalize_movement_type(values.get("movement_type"))
        if movement_type not in {"in", "out"}:
            raise StockMovementOperationError("movement_type must be in or out")
        catalog_item_id = self._normalize_required(values.get("catalog_item_id"), "catalog_item_id")
        quantity = self._parse_quantity(values.get("quantity"))
        movement_date = values.get("movement_date")
        if movement_date is None:
            raise StockMovementOperationError("movement_date is required")
        return {
            "catalog_item_id": catalog_item_id,
            "movement_type": movement_type,
            "quantity": quantity,
            "movement_date": movement_date,
            "notes": self._normalize_text(values.get("notes")),
            "reference_number": self._normalize_text(values.get("reference_number")),
            "procurement_id": self._normalize_text(values.get("procurement_id")),
        }

    def _parse_quantity(self, value: Any) -> Decimal:
        if value is None:
            raise StockMovementOperationError("quantity is required")
        quantity = Decimal(str(value))
        if quantity <= 0:
            raise StockMovementOperationError("quantity must be greater than 0")
        return quantity

    def _normalize_movement_type(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().lower()
        return normalized or None

    def _normalize_text(self, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _normalize_required(self, value: Any, field_name: str) -> str:
        normalized = self._normalize_text(value)
        if normalized is None:
            raise StockMovementOperationError(f"{field_name} is required")
        return normalized
