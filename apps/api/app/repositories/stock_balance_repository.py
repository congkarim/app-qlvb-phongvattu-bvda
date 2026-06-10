from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.materials_catalog import MaterialsCatalogItem
from app.models.stock_balance import StockBalance


class StockBalanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_catalog_item_id(self, catalog_item_id: str) -> StockBalance | None:
        stmt = select(StockBalance).where(
            StockBalance.catalog_item_id == catalog_item_id,
            StockBalance.deleted_at.is_(None),
        )
        return self.db.scalar(stmt)

    def get_or_create(self, catalog_item_id: str) -> StockBalance:
        balance = self.get_by_catalog_item_id(catalog_item_id)
        if balance is not None:
            return balance
        balance = StockBalance(catalog_item_id=catalog_item_id, quantity=Decimal("0"))
        self.db.add(balance)
        self.db.flush()
        return balance

    def update_quantity(self, balance: StockBalance, quantity: Decimal) -> StockBalance:
        balance.quantity = quantity
        self.db.add(balance)
        self.db.flush()
        return balance

    def list_low_stock(self, *, limit: int) -> list[tuple[MaterialsCatalogItem, StockBalance]]:
        stmt = (
            select(MaterialsCatalogItem, StockBalance)
            .join(StockBalance, StockBalance.catalog_item_id == MaterialsCatalogItem.id)
            .where(
                MaterialsCatalogItem.deleted_at.is_(None),
                MaterialsCatalogItem.is_active.is_(True),
                MaterialsCatalogItem.min_stock_level.is_not(None),
                StockBalance.deleted_at.is_(None),
                StockBalance.quantity <= MaterialsCatalogItem.min_stock_level,
            )
            .order_by(StockBalance.quantity.asc(), MaterialsCatalogItem.name.asc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).all())

    def count_low_stock(self) -> int:
        stmt = (
            select(func.count(MaterialsCatalogItem.id))
            .join(StockBalance, StockBalance.catalog_item_id == MaterialsCatalogItem.id)
            .where(
                MaterialsCatalogItem.deleted_at.is_(None),
                MaterialsCatalogItem.is_active.is_(True),
                MaterialsCatalogItem.min_stock_level.is_not(None),
                StockBalance.deleted_at.is_(None),
                StockBalance.quantity <= MaterialsCatalogItem.min_stock_level,
            )
        )
        return int(self.db.scalar(stmt) or 0)

    def get_balance_for_catalog(self, catalog_item_id: str) -> Decimal:
        balance = self.get_by_catalog_item_id(catalog_item_id)
        if balance is None:
            return Decimal("0")
        return balance.quantity
