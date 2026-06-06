from __future__ import annotations

import io
import sys
from unittest.mock import Mock

from app.core.config import get_settings
from app.services.document_service import DocumentService, UploadTooLargeError, UploadTooManyFilesError
from fastapi import UploadFile


def run_smoke() -> dict[str, object]:
    settings = get_settings()
    original_file_limit = settings.upload_max_file_size_bytes
    original_file_count = settings.upload_max_files_per_request
    settings.upload_max_file_size_bytes = 32
    settings.upload_max_files_per_request = 2

    try:
        service = DocumentService(db=Mock())
        oversized = UploadFile(filename="oversized.txt", file=io.BytesIO(b"x" * 64))
        try:
            service._save_upload_file(oversized, settings.upload_dir)
        except UploadTooLargeError:
            pass
        else:
            raise RuntimeError("Expected UploadTooLargeError for oversized file")

        try:
            service._validate_file_count(3)
        except UploadTooManyFilesError:
            pass
        else:
            raise RuntimeError("Expected UploadTooManyFilesError for too many files")

        return {
            "upload_max_file_size_bytes": original_file_limit,
            "upload_max_files_per_request": original_file_count,
            "oversized_rejected": True,
            "file_count_rejected": True,
        }
    finally:
        settings.upload_max_file_size_bytes = original_file_limit
        settings.upload_max_files_per_request = original_file_count


def main() -> int:
    result = run_smoke()
    print(result)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
