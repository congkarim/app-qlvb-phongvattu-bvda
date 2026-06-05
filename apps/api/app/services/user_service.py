from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository


VALID_ROLES = {"admin", "user"}


class UserNotFoundError(ValueError):
    pass


class UserAlreadyExistsError(ValueError):
    pass


class UserOperationError(ValueError):
    pass


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_logs = AuditLogRepository(db)
        self.users = UserRepository(db)

    def list_users(
        self,
        *,
        limit: int,
        offset: int,
        query: str | None,
        role: str | None,
        is_active: bool | None,
        sort_by: str,
        sort_dir: str,
    ) -> tuple[list[User], int]:
        users = self.users.list_users(
            limit=limit,
            offset=offset,
            query=query,
            role=role,
            is_active=is_active,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        total = self.users.count_users(query=query, role=role, is_active=is_active)
        return users, total

    def list_user_audit_logs(self, *, user_id: str, limit: int) -> list[AuditLog]:
        self._get_user(user_id, include_deleted=True)
        return self.audit_logs.list_for_entity(entity_type="user", entity_id=user_id, limit=limit)

    def create_user(
        self,
        *,
        email: str,
        full_name: str,
        password: str,
        role: str,
        is_active: bool,
        actor: User,
    ) -> User:
        role = self._validate_role(role)
        normalized_email = self._normalize_email(email)
        if self.users.get_by_email(normalized_email):
            raise UserAlreadyExistsError("User email already exists")

        user = self.users.create(
            email=normalized_email,
            full_name=full_name.strip(),
            password_hash=hash_password(password),
            role=role,
            is_active=is_active,
        )
        self.audit_logs.create(
            action="user.created",
            entity_type="user",
            entity_id=user.id,
            actor_user_id=actor.id,
            metadata={"email": user.email, "role": user.role, "is_active": user.is_active},
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(
        self,
        *,
        user_id: str,
        full_name: str,
        role: str,
        is_active: bool,
        actor: User,
    ) -> User:
        user = self._get_user(user_id)
        role = self._validate_role(role)
        if user.id == actor.id and user.role != role:
            raise UserOperationError("Admin cannot change their own role")
        if user.id == actor.id and user.is_active and not is_active:
            raise UserOperationError("Admin cannot deactivate their own account")

        old_role = user.role
        old_is_active = user.is_active
        user = self.users.update_profile(user, full_name=full_name.strip(), is_active=is_active)
        if user.role != role:
            user = self.users.update_role(user, role)
        self.audit_logs.create(
            action="user.updated",
            entity_type="user",
            entity_id=user.id,
            actor_user_id=actor.id,
            metadata={
                "email": user.email,
                "old_role": old_role,
                "new_role": user.role,
                "old_is_active": old_is_active,
                "new_is_active": user.is_active,
            },
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_user_active(self, *, user_id: str, is_active: bool, actor: User) -> User:
        user = self._get_user(user_id)
        if user.id == actor.id and user.is_active and not is_active:
            raise UserOperationError("Admin cannot deactivate their own account")
        old_is_active = user.is_active
        user = self.users.set_active(user, is_active)
        self.audit_logs.create(
            action="user.activated" if is_active else "user.deactivated",
            entity_type="user",
            entity_id=user.id,
            actor_user_id=actor.id,
            metadata={"email": user.email, "old_is_active": old_is_active, "new_is_active": user.is_active},
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def reset_password(self, *, user_id: str, password: str, actor: User) -> User:
        user = self._get_user(user_id)
        user = self.users.update_password(user, hash_password(password))
        self.audit_logs.create(
            action="user.password_reset",
            entity_type="user",
            entity_id=user.id,
            actor_user_id=actor.id,
            metadata={"email": user.email},
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def soft_delete_user(self, *, user_id: str, actor: User) -> User:
        user = self._get_user(user_id)
        if user.id == actor.id:
            raise UserOperationError("Admin cannot delete their own account")
        user = self.users.soft_delete(user)
        self.audit_logs.create(
            action="user.deleted",
            entity_type="user",
            entity_id=user.id,
            actor_user_id=actor.id,
            metadata={"email": user.email, "role": user.role},
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def _get_user(self, user_id: str, *, include_deleted: bool = False) -> User:
        user = self.users.get_by_id(user_id, include_deleted=include_deleted)
        if user is None:
            raise UserNotFoundError("User not found")
        return user

    def _validate_role(self, role: str) -> str:
        if role not in VALID_ROLES:
            raise UserOperationError("Invalid user role")
        return role

    def _normalize_email(self, email: str) -> str:
        normalized = email.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise UserOperationError("Invalid email")
        return normalized
