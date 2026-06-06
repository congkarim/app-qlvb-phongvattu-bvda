from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.db.session import SessionLocal
from app.routers import auth, catalogs, contracts, documents, health, ops, search, users
from app.services.auth_service import AuthService


settings = get_settings()
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        AuthService(db).seed_admin_user()
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(catalogs.router, prefix=settings.api_prefix)
app.include_router(catalogs.admin_router, prefix=settings.api_prefix)
app.include_router(contracts.router, prefix=settings.api_prefix)
app.include_router(documents.router, prefix=settings.api_prefix)
app.include_router(search.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(ops.router, prefix=settings.api_prefix)
