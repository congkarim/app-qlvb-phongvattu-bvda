from app.core.logging_config import configure_logging
from app.db.session import SessionLocal
from app.workers.ocr_worker import run_forever


if __name__ == "__main__":
    configure_logging()
    run_forever(SessionLocal)
