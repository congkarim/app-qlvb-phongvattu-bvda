from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from docx import Document as DocxDocument
from openpyxl import load_workbook
from PIL import Image
from xlrd import open_workbook


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
    _shared_ocr_engine: Any | None = None

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
                    bitmap = page.render(scale=2.0)
                    image = bitmap.to_pil()
                    pages.append(self._ocr_pil_image(image, page_number=page_index + 1))
                finally:
                    page.close()
        finally:
            pdf.close()
        return pages

    def _ocr_image_file(self, file_path: Path, page_number: int) -> DocumentPageContent:
        image = Image.open(file_path)
        try:
            return self._ocr_pil_image(image, page_number=page_number)
        finally:
            image.close()

    def _ocr_pil_image(self, image: Image.Image, page_number: int) -> DocumentPageContent:
        rgb_image = image.convert("RGB")
        image_array = np.array(rgb_image)
        preprocessed = self._preprocess_image(image_array)
        return self._run_paddleocr(preprocessed, page_number=page_number)

    def _preprocess_image(self, image_array: np.ndarray) -> np.ndarray:
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
        result = self._get_ocr_engine().ocr(image_array, cls=True)
        lines = self._extract_ocr_lines(result)
        text = "\n".join(line_text for line_text, _confidence in lines)
        confidence = sum(confidence for _line_text, confidence in lines) / len(lines) if lines else 0.0
        return DocumentPageContent(page_number=page_number, text=text, confidence=round(confidence, 4))

    def _get_ocr_engine(self) -> Any:
        if DocumentContentService._shared_ocr_engine is None:
            from paddleocr import PaddleOCR

            DocumentContentService._shared_ocr_engine = PaddleOCR(
                lang="vi",
                use_angle_cls=True,
                show_log=False,
                use_gpu=False,
            )
        return DocumentContentService._shared_ocr_engine

    def _extract_ocr_lines(self, result: Any) -> list[tuple[str, float]]:
        lines: list[tuple[str, float]] = []
        for page_result in result or []:
            for item in page_result or []:
                if len(item) < 2:
                    continue
                text_payload = item[1]
                if not isinstance(text_payload, (list, tuple)) or len(text_payload) < 2:
                    continue
                text = self._clean_text(str(text_payload[0]))
                if not text:
                    continue
                try:
                    confidence = float(text_payload[1])
                except (TypeError, ValueError):
                    confidence = 0.0
                lines.append((text, confidence))
        return lines

    def _clean_text(self, text: str) -> str:
        return " ".join(text.replace("\x00", " ").split())
