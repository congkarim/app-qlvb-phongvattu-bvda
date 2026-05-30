from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        return self.db.scalar(stmt)

    def create(self, *, email: str, full_name: str, password_hash: str, is_active: bool = True) -> User:
        user = User(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            is_active=is_active,
        )
        self.db.add(user)
        self.db.flush()
        return user
