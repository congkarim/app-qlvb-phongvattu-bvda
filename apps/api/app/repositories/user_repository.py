from datetime import datetime, timezone

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def get_by_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def list_users(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        query: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> list[User]:
        stmt = select(User).where(User.deleted_at.is_(None))
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
        if role:
            stmt = stmt.where(User.role == role)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        sortable_columns = {
            "created_at": User.created_at,
            "updated_at": User.updated_at,
            "email": User.email,
            "full_name": User.full_name,
            "role": User.role,
            "is_active": User.is_active,
        }
        direction = asc if sort_dir == "asc" else desc
        sort_column = sortable_columns.get(sort_by, User.created_at)
        stmt = stmt.order_by(direction(sort_column), User.created_at.desc()).limit(limit).offset(offset)
        return list(self.db.scalars(stmt))

    def count_users(
        self,
        *,
        query: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(User).where(User.deleted_at.is_(None))
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
        if role:
            stmt = stmt.where(User.role == role)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        return int(self.db.scalar(stmt) or 0)

    def create(
        self,
        *,
        email: str,
        full_name: str,
        password_hash: str,
        role: str = "user",
        is_active: bool = True,
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            role=role,
            is_active=is_active,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update_profile(self, user: User, *, full_name: str, is_active: bool) -> User:
        user.full_name = full_name
        user.is_active = is_active
        self.db.add(user)
        self.db.flush()
        return user

    def update_role(self, user: User, role: str) -> User:
        user.role = role
        self.db.add(user)
        self.db.flush()
        return user

    def update_password(self, user: User, password_hash: str) -> User:
        user.password_hash = password_hash
        self.db.add(user)
        self.db.flush()
        return user

    def set_active(self, user: User, is_active: bool) -> User:
        user.is_active = is_active
        self.db.add(user)
        self.db.flush()
        return user

    def soft_delete(self, user: User) -> User:
        user.deleted_at = datetime.now(timezone.utc)
        user.is_active = False
        self.db.add(user)
        self.db.flush()
        return user
