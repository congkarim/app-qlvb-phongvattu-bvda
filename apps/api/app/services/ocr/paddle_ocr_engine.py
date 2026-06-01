from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import Settings
from app.services.ocr.schemas import OcrLine


class PaddleOcrEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._engine: Any | None = None

    def recognize(self, image_array: np.ndarray) -> list[OcrLine]:
        result = self._run(image_array)
        return self.extract_lines(result)

    def detect(self, image_array: np.ndarray) -> list[OcrLine]:
        result = self._run(image_array)
        lines = self.extract_lines(result)
        return [line for line in lines if line.box]

    def _run(self, image_array: np.ndarray) -> Any:
        engine = self._get_engine()
        if hasattr(engine, "predict"):
            return engine.predict(image_array)
        return engine.ocr(image_array, cls=True)

    def _get_engine(self) -> Any:
        if self._engine is None:
            from paddleocr import PaddleOCR

            self._engine = self._create_engine(PaddleOCR)
        return self._engine

    def _create_engine(self, paddleocr_class: Any) -> Any:
        common_kwargs = {"lang": self.settings.ocr_lang}
        try:
            return paddleocr_class(
                **common_kwargs,
                **self._paddleocr_v3_model_kwargs(),
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                device="gpu" if self.settings.ocr_use_gpu else self.settings.ocr_device,
            )
        except (TypeError, ValueError):
            return paddleocr_class(
                **common_kwargs,
                use_angle_cls=True,
                show_log=False,
                use_gpu=self.settings.ocr_use_gpu,
            )

    def _paddleocr_v3_model_kwargs(self) -> dict[str, str]:
        model_dir = self.settings.ocr_model_dir
        kwargs: dict[str, str] = {}
        detection_dir = model_dir / "PP-OCRv5_server_det"
        if detection_dir.exists():
            kwargs["text_detection_model_name"] = "PP-OCRv5_server_det"
            kwargs["text_detection_model_dir"] = str(detection_dir)
        recognition_dir = model_dir / "latin_PP-OCRv5_mobile_rec"
        if recognition_dir.exists():
            kwargs["text_recognition_model_name"] = "latin_PP-OCRv5_mobile_rec"
            kwargs["text_recognition_model_dir"] = str(recognition_dir)
        return kwargs

    def extract_lines(self, result: Any) -> list[OcrLine]:
        v3_lines = self._extract_paddleocr_v3_lines(result)
        if v3_lines:
            return v3_lines
        return self._extract_paddleocr_v2_lines(result)

    def _extract_paddleocr_v3_lines(self, result: Any) -> list[OcrLine]:
        lines: list[OcrLine] = []
        for page_result in result or []:
            payload = self._paddleocr_v3_payload(page_result)
            if not payload:
                continue
            texts = payload.get("rec_texts") or []
            scores = payload.get("rec_scores") or []
            boxes = payload.get("rec_polys") or payload.get("dt_polys") or payload.get("rec_boxes") or []
            for index, raw_text in enumerate(texts):
                text = str(raw_text).strip()
                if not text:
                    continue
                try:
                    confidence = float(scores[index])
                except (IndexError, TypeError, ValueError):
                    confidence = 0.0
                if confidence < self.settings.ocr_min_confidence:
                    continue
                lines.append(
                    OcrLine(
                        text=text,
                        confidence=confidence,
                        box=self._parse_box(boxes[index]) if index < len(boxes) else None,
                    )
                )
        return lines

    def _paddleocr_v3_payload(self, page_result: Any) -> dict[str, Any] | None:
        if isinstance(page_result, dict):
            payload = page_result
        else:
            payload = getattr(page_result, "json", None)
            if callable(payload):
                payload = payload()
        if not isinstance(payload, dict):
            return None
        result_payload = payload.get("res", payload)
        return result_payload if isinstance(result_payload, dict) else None

    def _extract_paddleocr_v2_lines(self, result: Any) -> list[OcrLine]:
        lines: list[OcrLine] = []
        for page_result in result or []:
            for item in page_result or []:
                if len(item) < 2:
                    continue
                text_payload = item[1]
                if not isinstance(text_payload, (list, tuple)) or len(text_payload) < 2:
                    continue
                text = str(text_payload[0]).strip()
                if not text:
                    continue
                try:
                    confidence = float(text_payload[1])
                except (TypeError, ValueError):
                    confidence = 0.0
                lines.append(OcrLine(text=text, confidence=confidence, box=self._parse_box(item[0])))
        return lines

    def _parse_box(self, raw_box: Any) -> tuple[tuple[float, float], ...] | None:
        if raw_box is None:
            return None
        array = np.asarray(raw_box, dtype=float)
        if array.ndim == 1 and array.size == 4:
            x1, y1, x2, y2 = array.tolist()
            return ((x1, y1), (x2, y1), (x2, y2), (x1, y2))
        if array.ndim == 2 and array.shape[1] >= 2:
            return tuple((float(point[0]), float(point[1])) for point in array)
        return None
