from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.core.config import Settings
from app.services.ocr.paddle_ocr_engine import PaddleOcrEngine
from app.services.ocr.schemas import OcrLine


class PaddleVietOcrEngine:
    def __init__(self, settings: Settings, detector: PaddleOcrEngine | None = None) -> None:
        self.settings = settings
        self.detector = detector or PaddleOcrEngine(settings)
        self._predictor = None

    def recognize(self, image_array: np.ndarray) -> list[OcrLine]:
        detected_lines = self.detector.detect(image_array)
        if not detected_lines:
            return []

        predictor = self._get_predictor()
        recognized_lines: list[OcrLine] = []
        for line in self._sort_lines(detected_lines):
            if not line.box:
                continue
            crop = self._crop_box(image_array, line.box)
            if crop is None:
                continue
            text, confidence = self._predict_crop(predictor, crop)
            if text:
                recognized_lines.append(OcrLine(text=text, confidence=confidence, box=line.box))
        return recognized_lines

    def _get_predictor(self):
        if self._predictor is not None:
            return self._predictor

        weight_path = self._vietocr_weight_path()
        if not weight_path.exists():
            raise FileNotFoundError(
                "VietOCR weight file not found. "
                f"Set VIETOCR_WEIGHT_PATH or place the model at {weight_path}."
            )

        from vietocr.tool.config import Cfg
        from vietocr.tool.predictor import Predictor

        config = Cfg.load_config_from_name(self.settings.vietocr_config)
        config["weights"] = str(weight_path)
        config["device"] = self.settings.vietocr_device
        config["cnn"]["pretrained"] = False
        config["predictor"]["beamsearch"] = self.settings.vietocr_beamsearch
        self._predictor = Predictor(config)
        return self._predictor

    def _vietocr_weight_path(self) -> Path:
        if self.settings.vietocr_weight_path:
            return self.settings.vietocr_weight_path
        return self.settings.vietocr_model_dir / "transformerocr.pth"

    def _predict_crop(self, predictor, crop: Image.Image) -> tuple[str, float]:
        prediction = predictor.predict(crop, return_prob=True)
        if isinstance(prediction, tuple):
            text = str(prediction[0]).strip()
            try:
                confidence = float(prediction[1])
            except (TypeError, ValueError):
                confidence = 0.0
            return text, confidence
        return str(prediction).strip(), 0.0

    def _sort_lines(self, lines: list[OcrLine]) -> list[OcrLine]:
        return sorted(lines, key=lambda line: (self._box_top(line.box), self._box_left(line.box)))

    def _box_top(self, box: tuple[tuple[float, float], ...] | None) -> float:
        return min((point[1] for point in box), default=0.0) if box else 0.0

    def _box_left(self, box: tuple[tuple[float, float], ...] | None) -> float:
        return min((point[0] for point in box), default=0.0) if box else 0.0

    def _crop_box(self, image_array: np.ndarray, box: tuple[tuple[float, float], ...]) -> Image.Image | None:
        points = np.asarray(box, dtype=np.float32)
        if points.ndim != 2 or points.shape[0] < 4 or points.shape[1] < 2:
            return None
        points = self._order_points(points[:4])
        width = int(max(np.linalg.norm(points[0] - points[1]), np.linalg.norm(points[2] - points[3])))
        height = int(max(np.linalg.norm(points[0] - points[3]), np.linalg.norm(points[1] - points[2])))
        if width <= 2 or height <= 2:
            return None

        destination = np.array(
            [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
            dtype=np.float32,
        )
        matrix = cv2.getPerspectiveTransform(points, destination)
        warped = cv2.warpPerspective(image_array, matrix, (width, height), borderValue=(255, 255, 255))
        return Image.fromarray(warped).convert("RGB")

    def _order_points(self, points: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype=np.float32)
        point_sum = points.sum(axis=1)
        point_diff = np.diff(points, axis=1).reshape(-1)
        rect[0] = points[np.argmin(point_sum)]
        rect[2] = points[np.argmax(point_sum)]
        rect[1] = points[np.argmin(point_diff)]
        rect[3] = points[np.argmax(point_diff)]
        return rect
