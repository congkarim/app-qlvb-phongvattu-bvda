from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def login(self, email: str, password: str) -> str | None:
        user = self.users.get_by_email(email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return create_access_token(subject=user.id, extra_claims={"email": user.email})

    def seed_admin_user(self) -> None:
        settings = get_settings()
        existing_user = self.users.get_by_email(settings.admin_email)
        if existing_user:
            return

        self.users.create(
            email=settings.admin_email,
            full_name=settings.admin_full_name,
            password_hash=hash_password(settings.admin_password),
            is_active=True,
        )
