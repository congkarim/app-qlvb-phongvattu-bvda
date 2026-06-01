from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import cv2
import numpy as np
from docx import Document as DocxDocument
from openpyxl import load_workbook
from PIL import Image
from xlrd import open_workbook

from app.core.config import get_settings


class UnsupportedDocumentFormatError(ValueError):
    pass


class EmptyDocumentContentError(ValueError):
    pass


@dataclass(frozen=True)
class DocumentPageContent:
    page_number: int
    text: str
    confidence: float


class DocumentContentService:
    TEXT_EXTENSIONS = {".txt", ".md"}
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
    MIN_NATIVE_PDF_TEXT_CHARS = 20
    _shared_ocr_engine: Any | None = None
    _OCR_LINE_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
        (
            re.compile(r"^C\s*NG\s+H(?:A|ÒA)\s+X\s+HI\s+CH\s+NGH(?:A|ÎA)\s+VI\s*T\s+NAM$", re.IGNORECASE),
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
        ),
        (
            re.compile(r"^Đ\s*c\s+l\s*p\s*-\s*T\s*do\s*-\s*H\s*nh\s+phúc$", re.IGNORECASE),
            "Độc lập - Tự do - Hạnh phúc",
        ),
    )
    _OCR_TERM_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
        (re.compile(r"\bĐiu\b", re.IGNORECASE), "Điều"),
        (re.compile(r"\bDiu\b", re.IGNORECASE), "Điều"),
        (re.compile(r"\bKhon\b", re.IGNORECASE), "Khoản"),
        (re.compile(r"\bPhm vi\b", re.IGNORECASE), "Phạm vi"),
        (re.compile(r"\bPhạm vi Điều chnh\b", re.IGNORECASE), "Phạm vi điều chỉnh"),
        (re.compile(r"\bđiu chnh\b", re.IGNORECASE), "điều chỉnh"),
        (re.compile(r"\bĐiều chnh\b", re.IGNORECASE), "điều chỉnh"),
        (re.compile(r"\bdieu chinh\b", re.IGNORECASE), "điều chỉnh"),
        (re.compile(r"\bđu thu\b", re.IGNORECASE), "đấu thầu"),
        (re.compile(r"\bdau thau\b", re.IGNORECASE), "đấu thầu"),
        (re.compile(r"\bVăn bn\b", re.IGNORECASE), "Văn bản"),
        (re.compile(r"\bVan ban\b", re.IGNORECASE), "Văn bản"),
        (re.compile(r"\bphai gi du ting Vit\b", re.IGNORECASE), "phải giữ dấu tiếng Việt"),
        (re.compile(r"\bphi gi du ting Vit\b", re.IGNORECASE), "phải giữ dấu tiếng Việt"),
    )

    def __init__(self) -> None:
        self.settings = get_settings()

    def extract_pages(self, file_path: Path, filename: str) -> list[DocumentPageContent]:
        if not file_path.exists():
            raise FileNotFoundError(f"Uploaded file not found: {file_path}")

        extension = self._extension(file_path, filename)
        if extension in self.TEXT_EXTENSIONS:
            pages = [DocumentPageContent(page_number=1, text=self._read_text(file_path), confidence=1.0)]
        elif extension == ".docx":
            pages = [DocumentPageContent(page_number=1, text=self._read_docx(file_path), confidence=1.0)]
        elif extension == ".xlsx":
            pages = self._read_xlsx(file_path)
        elif extension == ".xls":
            pages = self._read_xls(file_path)
        elif extension == ".doc":
            raise UnsupportedDocumentFormatError(
                "Legacy .doc is not supported yet. Convert the file to .docx or .pdf and upload again."
            )
        elif extension == ".pdf":
            pages = self._ocr_pdf(file_path)
        elif extension in self.IMAGE_EXTENSIONS:
            pages = [self._ocr_image_file(file_path, page_number=1)]
        else:
            raise UnsupportedDocumentFormatError(f"Unsupported file extension: {extension or 'unknown'}")

        non_empty_pages = [page for page in pages if page.text.strip()]
        if not non_empty_pages:
            raise EmptyDocumentContentError(f"No text content extracted from {filename}")
        return pages

    def _extension(self, file_path: Path, filename: str) -> str:
        return (Path(filename).suffix or file_path.suffix).lower()

    def _read_text(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8", errors="ignore")

    def _read_docx(self, file_path: Path) -> str:
        document = DocxDocument(file_path)
        parts: list[str] = []

        for paragraph in document.paragraphs:
            text = self._clean_text(paragraph.text)
            if text:
                parts.append(text)

        for table_index, table in enumerate(document.tables, start=1):
            parts.append(f"Bảng {table_index}")
            for row in table.rows:
                cells = [self._clean_text(cell.text) for cell in row.cells]
                row_text = " | ".join(cell for cell in cells if cell)
                if row_text:
                    parts.append(row_text)

        return "\n".join(parts)

    def _read_xlsx(self, file_path: Path) -> list[DocumentPageContent]:
        workbook = load_workbook(file_path, read_only=True, data_only=True)
        pages: list[DocumentPageContent] = []
        try:
            for page_number, sheet in enumerate(workbook.worksheets, start=1):
                pages.append(
                    DocumentPageContent(
                        page_number=page_number,
                        text=self._sheet_to_text(sheet.title, sheet.iter_rows(values_only=True)),
                        confidence=1.0,
                    )
                )
        finally:
            workbook.close()
        return pages

    def _read_xls(self, file_path: Path) -> list[DocumentPageContent]:
        workbook = open_workbook(str(file_path), on_demand=True)
        pages: list[DocumentPageContent] = []
        try:
            for page_number, sheet_name in enumerate(workbook.sheet_names(), start=1):
                sheet = workbook.sheet_by_name(sheet_name)
                rows = (sheet.row_values(row_index) for row_index in range(sheet.nrows))
                pages.append(
                    DocumentPageContent(
                        page_number=page_number,
                        text=self._sheet_to_text(sheet_name, rows),
                        confidence=1.0,
                    )
                )
        finally:
            workbook.release_resources()
        return pages

    def _sheet_to_text(self, sheet_name: str, rows: Any) -> str:
        lines = [f"Sheet: {sheet_name}"]
        for row_number, row in enumerate(rows, start=1):
            values = [self._format_cell_value(value) for value in row]
            row_text = " | ".join(value for value in values if value)
            if row_text:
                lines.append(f"Row {row_number}: {row_text}")
        return "\n".join(lines)

    def _format_cell_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return self._clean_text(str(value))

    def _ocr_pdf(self, file_path: Path) -> list[DocumentPageContent]:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(file_path))
        pages: list[DocumentPageContent] = []
        try:
            for page_index in range(len(pdf)):
                page = pdf[page_index]
                try:
                    page_number = page_index + 1
                    native_text = self._extract_native_pdf_text(page)
                    if len(native_text) >= self.MIN_NATIVE_PDF_TEXT_CHARS:
                        pages.append(
                            DocumentPageContent(page_number=page_number, text=native_text, confidence=1.0)
                        )
                        continue

                    bitmap = page.render(scale=2.0)
                    image = bitmap.to_pil()
                    pages.append(self._ocr_pil_image(image, page_number=page_number))
                finally:
                    page.close()
        finally:
            pdf.close()
        return pages

    def _extract_native_pdf_text(self, page: Any) -> str:
        try:
            text_page = page.get_textpage()
            try:
                char_count = text_page.count_chars()
                if char_count <= 0:
                    return ""
                return self._clean_multiline_text(text_page.get_text_range(0, char_count))
            finally:
                close = getattr(text_page, "close", None)
                if close:
                    close()
        except Exception:
            return ""

    def _ocr_image_file(self, file_path: Path, page_number: int) -> DocumentPageContent:
        image = Image.open(file_path)
        try:
            return self._ocr_pil_image(image, page_number=page_number)
        finally:
            image.close()

    def _ocr_pil_image(self, image: Image.Image, page_number: int) -> DocumentPageContent:
        rgb_image = image.convert("RGB")
        image_array = np.array(rgb_image)
        candidates = self._preprocess_image_candidates(image_array)
        results = [self._run_paddleocr(candidate, page_number=page_number) for candidate in candidates]
        return max(results, key=self._ocr_result_score)

    def _preprocess_image_candidates(self, image_array: np.ndarray) -> list[np.ndarray]:
        mode = self.settings.ocr_preprocess_mode.lower()
        if mode == "raw":
            return [self._resize_for_ocr(image_array)]
        if mode == "clahe":
            return [self._preprocess_clahe(image_array)]
        if mode == "threshold":
            return [self._preprocess_threshold(image_array)]
        if mode != "auto":
            raise ValueError(f"Unsupported OCR_PREPROCESS_MODE: {self.settings.ocr_preprocess_mode}")

        raw = self._resize_for_ocr(image_array)
        clahe = self._preprocess_clahe(image_array)
        thresholded = self._preprocess_threshold(image_array)
        return [raw, clahe, thresholded]

    def _resize_for_ocr(self, image_array: np.ndarray) -> np.ndarray:
        height, width = image_array.shape[:2]
        if min(height, width) >= 1200:
            return image_array

        scale = 1200 / max(min(height, width), 1)
        return cv2.resize(image_array, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    def _preprocess_clahe(self, image_array: np.ndarray) -> np.ndarray:
        resized = self._resize_for_ocr(image_array)
        lab = cv2.cvtColor(resized, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_l = clahe.apply(l_channel)
        enhanced = cv2.merge((enhanced_l, a_channel, b_channel))
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)

    def _preprocess_threshold(self, image_array: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        height, width = gray.shape[:2]
        if min(height, width) < 1200:
            scale = 1200 / max(min(height, width), 1)
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        thresholded = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )
        return cv2.cvtColor(thresholded, cv2.COLOR_GRAY2RGB)

    def _run_paddleocr(self, image_array: np.ndarray, page_number: int) -> DocumentPageContent:
        result = self._run_ocr_engine(image_array)
        lines = self._extract_ocr_lines(result)
        text = "\n".join(line_text for line_text, _confidence in lines)
        confidence = sum(confidence for _line_text, confidence in lines) / len(lines) if lines else 0.0
        return DocumentPageContent(page_number=page_number, text=text, confidence=round(confidence, 4))

    def _run_ocr_engine(self, image_array: np.ndarray) -> Any:
        engine = self._get_ocr_engine()
        if hasattr(engine, "predict"):
            return engine.predict(image_array)
        return engine.ocr(image_array, cls=True)

    def _get_ocr_engine(self) -> Any:
        if DocumentContentService._shared_ocr_engine is None:
            if self.settings.ocr_engine.lower() != "paddleocr":
                raise ValueError(f"Unsupported OCR_ENGINE: {self.settings.ocr_engine}")
            from paddleocr import PaddleOCR

            DocumentContentService._shared_ocr_engine = self._create_paddleocr_engine(PaddleOCR)
        return DocumentContentService._shared_ocr_engine

    def _create_paddleocr_engine(self, paddleocr_class: Any) -> Any:
        common_kwargs = {
            "lang": self.settings.ocr_lang,
        }
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
        model_paths = {
            "text_detection_model_dir": model_dir / "PP-OCRv5_server_det",
            "text_recognition_model_dir": model_dir / "latin_PP-OCRv5_mobile_rec",
        }
        return {
            key: str(path)
            for key, path in model_paths.items()
            if path.exists()
        }

    def _extract_ocr_lines(self, result: Any) -> list[tuple[str, float]]:
        v3_lines = self._extract_paddleocr_v3_lines(result)
        if v3_lines:
            return v3_lines

        lines: list[tuple[str, float]] = []
        for page_result in result or []:
            for item in page_result or []:
                if len(item) < 2:
                    continue
                text_payload = item[1]
                if not isinstance(text_payload, (list, tuple)) or len(text_payload) < 2:
                    continue
                text = self._clean_ocr_text(str(text_payload[0]))
                if not text:
                    continue
                try:
                    confidence = float(text_payload[1])
                except (TypeError, ValueError):
                    confidence = 0.0
                lines.append((text, confidence))
        return lines

    def _extract_paddleocr_v3_lines(self, result: Any) -> list[tuple[str, float]]:
        lines: list[tuple[str, float]] = []
        for page_result in result or []:
            payload = self._paddleocr_v3_payload(page_result)
            if not payload:
                continue
            texts = payload.get("rec_texts") or []
            scores = payload.get("rec_scores") or []
            for index, raw_text in enumerate(texts):
                text = self._clean_ocr_text(str(raw_text))
                if not text:
                    continue
                try:
                    confidence = float(scores[index])
                except (IndexError, TypeError, ValueError):
                    confidence = 0.0
                if confidence < self.settings.ocr_min_confidence:
                    continue
                lines.append((text, confidence))
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

    def _ocr_result_score(self, page_content: DocumentPageContent) -> tuple[float, int, int]:
        return (
            page_content.confidence,
            self._count_vietnamese_accent_chars(page_content.text),
            len(page_content.text),
        )

    def _count_vietnamese_accent_chars(self, text: str) -> int:
        vietnamese_chars = set(
            "ăâđêôơưáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩị"
            "óòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"
            "ĂÂĐÊÔƠƯÁÀẢÃẠẮẰẲẴẶẤẦẨẪẬÉÈẺẼẸẾỀỂỄỆÍÌỈĨỊ"
            "ÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴ"
        )
        return sum(1 for char in text if char in vietnamese_chars)

    def _clean_text(self, text: str) -> str:
        return " ".join(text.replace("\x00", " ").split())

    def _clean_ocr_text(self, text: str) -> str:
        cleaned = self._clean_text(text)
        if not self.settings.ocr_restore_vietnamese_terms:
            return cleaned

        for pattern, replacement in self._OCR_LINE_REPLACEMENTS:
            if pattern.fullmatch(cleaned):
                return replacement

        restored = cleaned
        for pattern, replacement in self._OCR_TERM_REPLACEMENTS:
            restored = pattern.sub(replacement, restored)
        return restored

    def _clean_multiline_text(self, text: str) -> str:
        lines = [
            self._clean_text(line)
            for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        ]
        return "\n".join(line for line in lines if line)
