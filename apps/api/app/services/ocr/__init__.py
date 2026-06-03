from __future__ import annotations

from app.core.config import Settings
from app.services.ocr.paddle_ocr_engine import PaddleOcrEngine
from app.services.ocr.paddle_vietocr_engine import PaddleVietOcrEngine
from app.services.ocr.schemas import OcrEngine


_ENGINES: dict[str, OcrEngine] = {}


def get_ocr_engine(settings: Settings, engine_name: str | None = None) -> OcrEngine:
    engine_name = (engine_name or settings.ocr_engine).lower()
    cache_key = ":".join(
        [
            engine_name,
            settings.ocr_lang,
            settings.ocr_device,
            str(settings.ocr_model_dir),
            settings.vietocr_config,
            str(settings.vietocr_weight_path),
            settings.vietocr_device,
        ]
    )
    if cache_key not in _ENGINES:
        if engine_name == "paddleocr":
            _ENGINES[cache_key] = PaddleOcrEngine(settings)
        elif engine_name == "paddle_vietocr":
            _ENGINES[cache_key] = PaddleVietOcrEngine(settings)
        else:
            raise ValueError(f"Unsupported OCR_ENGINE: {settings.ocr_engine}")
    return _ENGINES[cache_key]
