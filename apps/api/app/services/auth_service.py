from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def login(self, email: str, password: str) -> tuple[str, User] | None:
        user = self.users.get_by_email(email.strip().lower())
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        token = create_access_token(subject=user.id, extra_claims={"email": user.email, "role": user.role})
        return token, user

    def seed_admin_user(self) -> None:
        settings = get_settings()
        admin_email = settings.admin_email.strip().lower()
        existing_user = self.users.get_by_email(admin_email)
        if existing_user:
            if existing_user.role != "admin":
                self.users.update_role(existing_user, "admin")
            return

        self.users.create(
            email=admin_email,
            full_name=settings.admin_full_name,
            password_hash=hash_password(settings.admin_password),
            role="admin",
            is_active=True,
        )
