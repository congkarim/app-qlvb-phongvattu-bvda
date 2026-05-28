from app.db.session import SessionLocal
from app.workers.ocr_worker import run_forever


if __name__ == "__main__":
    run_forever(SessionLocal)
