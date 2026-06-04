from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import re
from typing import Protocol
import unicodedata


DOCUMENT_TYPE_LABELS = {
    "NQ": "Nghị quyết (cá biệt)",
    "QĐ": "Quyết định (cá biệt)",
    "CT": "Chỉ thị",
    "QC": "Quy chế",
    "QYĐ": "Quy định",
    "TC": "Thông cáo",
    "TB": "Thông báo",
    "HD": "Hướng dẫn",
    "CTr": "Chương trình",
    "KH": "Kế hoạch",
    "PA": "Phương án",
    "ĐA": "Đề án",
    "DA": "Dự án",
    "BC": "Báo cáo",
    "BB": "Biên bản",
    "TTr": "Tờ trình",
    "HĐ": "Hợp đồng",
    "CV": "Công văn",
    "CĐ": "Công điện",
    "BGN": "Bản ghi nhớ",
    "BTT": "Bản thỏa thuận",
    "GUQ": "Giấy ủy quyền",
    "GM": "Giấy mời",
    "GGT": "Giấy giới thiệu",
    "GNP": "Giấy nghỉ phép",
    "PG": "Phiếu gửi",
    "PC": "Phiếu chuyển",
    "PB": "Phiếu báo",
    "TCg": "Thư công",
    "UNKNOWN": "Không đủ dữ liệu hoặc OCR quá lỗi",
}


class TextPage(Protocol):
    text: str


@dataclass(frozen=True)
class DocumentClassificationResult:
    document_type: str
    confidence: float
    agency_name: str | None = None
    document_number: str | None = None
    symbol: str | None = None
    date: date | None = None
    place: str | None = None
    title: str | None = None
    excerpt: str | None = None
    recipient: str | None = None
    signer_name: str | None = None
    signer_title: str | None = None
    seals_present: bool | None = None
    attachment_present: bool | None = None
    page_count: int | None = None

    def to_audit_metadata(self) -> dict:
        payload = asdict(self)
        if self.date:
            payload["date"] = self.date.isoformat()
        return payload


class DocumentClassifierService:
    _TYPE_PATTERNS: tuple[tuple[str, str, float], ...] = (
        ("QĐ", r"\bQUY[ẾE]T\s+ĐỊNH\b", 0.94),
        ("TB", r"\bTH[ÔO]NG\s+B[ÁA]O\b", 0.93),
        ("BB", r"\bBI[ÊE]N\s+B[ẢA]N\b", 0.92),
        ("TTr", r"\bT[ỜO]\s+TR[ÌI]NH\b", 0.91),
        ("GM", r"\bGI[ẤA]Y\s+M[ỜO]I\b", 0.91),
        ("GGT", r"\bGI[ẤA]Y\s+GI[ỚO]I\s+THI[ỆE]U\b", 0.91),
        ("GUQ", r"\bGI[ẤA]Y\s+[ỦU]Y\s+QUY[ỀE]N\b", 0.91),
        ("GNP", r"\bGI[ẤA]Y\s+NGH[ỈI]\s+PH[ÉE]P\b", 0.90),
        ("BC", r"\bB[ÁA]O\s+C[ÁA]O\b", 0.90),
        ("KH", r"\bK[ẾE]\s+HO[ẠA]CH\b", 0.90),
        ("HD", r"\bH[ƯU]ỚNG\s+D[ẪA]N\b", 0.90),
        ("CTr", r"\bCH[ƯU]ƠNG\s+TR[ÌI]NH\b", 0.90),
        ("PA", r"\bPH[ƯU]ƠNG\s+[ÁA]N\b", 0.90),
        ("ĐA", r"\bĐ[ỀE]\s+[ÁA]N\b", 0.90),
        ("DA", r"\bD[ỰU]\s+[ÁA]N\b", 0.88),
        ("HĐ", r"\bH[ỢO]P\s+Đ[ỒO]NG\b", 0.90),
        ("CĐ", r"\bC[ÔO]NG\s+ĐI[ỆE]N\b", 0.90),
        ("NQ", r"\bNGH[ỊI]\s+QUY[ẾE]T\b", 0.90),
        ("QC", r"\bQUY\s+CH[ẾE]\b", 0.90),
        ("QYĐ", r"\bQUY\s+Đ[ỊI]NH\b", 0.90),
        ("TC", r"\bTH[ÔO]NG\s+C[ÁA]O\b", 0.90),
        ("BGN", r"\bB[ẢA]N\s+GHI\s+NH[ỚO]\b", 0.89),
        ("BTT", r"\bB[ẢA]N\s+TH[ỎO]A\s+THU[ẬA]N\b", 0.89),
        ("PG", r"\bPHI[ẾE]U\s+G[ỬU]I\b", 0.88),
        ("PC", r"\bPHI[ẾE]U\s+CHUY[ỂE]N\b", 0.88),
        ("PB", r"\bPHI[ẾE]U\s+B[ÁA]O\b", 0.88),
        ("TCg", r"\bTH[ƯU]\s+C[ÔO]NG\b", 0.86),
    )

    def classify(self, pages: list[TextPage]) -> DocumentClassificationResult:
        normalized_pages = [self._normalize_text(page.text) for page in pages]
        full_text = "\n".join(normalized_pages)
        first_page = normalized_pages[0] if normalized_pages else ""
        document_type, confidence = self._detect_document_type(first_page, full_text)

        document_number, symbol = self._extract_document_number_and_symbol(first_page)
        place, issued_date = self._extract_place_and_date(first_page)
        title = self._extract_title(first_page, document_type)
        excerpt = self._extract_excerpt(first_page)
        recipient = self._extract_recipient(full_text)
        signer_title, signer_name = self._extract_signer(full_text)

        if document_type == "UNKNOWN":
            confidence = min(confidence, 0.45)
        elif excerpt or document_number or title:
            confidence = min(confidence + 0.03, 0.98)

        return DocumentClassificationResult(
            document_type=document_type,
            confidence=round(confidence, 2),
            agency_name=self._extract_agency_name(first_page),
            document_number=document_number,
            symbol=symbol,
            date=issued_date,
            place=place,
            title=title,
            excerpt=excerpt,
            recipient=recipient,
            signer_name=signer_name,
            signer_title=signer_title,
            seals_present=self._detect_seal(full_text),
            attachment_present=self._detect_attachment(full_text),
            page_count=len(pages) or None,
        )

    def _normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFC", text or "")
        replacements = (
            (r"\bQD\b", "QĐ"),
            (r"\bQÐ\b", "QĐ"),
            (r"\bV\s*/\s*v\b", "V/v"),
            (r"\bS[ôo0]\s*[:：]\s*", "Số: "),
            (r"\bngay\b", "ngày"),
            (r"\bthang\b", "tháng"),
            (r"\bnam\b", "năm"),
        )
        for pattern, replacement in replacements:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        lines = [" ".join(line.strip().split()) for line in normalized.splitlines()]
        return "\n".join(line for line in lines if line)

    def _detect_document_type(self, first_page: str, full_text: str) -> tuple[str, float]:
        search_text = "\n".join(first_page.splitlines()[:30]) or full_text[:3000]
        for label, pattern, confidence in self._TYPE_PATTERNS:
            if re.search(pattern, search_text, flags=re.IGNORECASE):
                return label, confidence
        if re.search(r"\bV/v\b", search_text, flags=re.IGNORECASE):
            return "CV", 0.86
        if re.search(r"\bK[íi]nh\s+g[ửu]i\b", search_text, flags=re.IGNORECASE):
            return "CV", 0.72
        return "UNKNOWN", 0.35

    def _extract_agency_name(self, first_page: str) -> str | None:
        lines = self._lines(first_page)
        for index, line in enumerate(lines[:10]):
            upper = line.upper()
            if "CỘNG HÒA" in upper or "ĐỘC LẬP" in upper:
                continue
            if upper.startswith(("SỐ:", "Số:".upper())):
                continue
            if 4 <= len(line) <= 255 and not self._looks_like_date_place(line):
                next_line = lines[index + 1] if index + 1 < len(lines) else ""
                if next_line and next_line.isupper() and len(next_line) <= 80:
                    return self._clean_value(f"{line} {next_line}", 255)
                return self._clean_value(line, 255)
        return None

    def _extract_document_number_and_symbol(self, first_page: str) -> tuple[str | None, str | None]:
        match = re.search(r"\bSố\s*:\s*([^\n]+)", first_page, flags=re.IGNORECASE)
        if not match:
            return None, None
        value = self._clean_value(match.group(1), 128)
        if not value:
            return None, None
        value = re.split(r"\s{2,}|(?=\b[A-ZÀ-Ỹ][a-zà-ỹ]+,\s*ngày\b)", value)[0].strip(" .;,")
        symbol = None
        if "/" in value:
            symbol = value.split("/", 1)[1].strip(" .;,") or None
        return value or None, self._clean_value(symbol, 128)

    def _extract_place_and_date(self, first_page: str) -> tuple[str | None, date | None]:
        pattern = (
            r"(?P<place>[A-ZÀ-Ỹ][A-Za-zÀ-ỹ\s\-.]{1,80})[, ]+"
            r"ngày\s+(?P<day>\d{1,2})\s+tháng\s+(?P<month>\d{1,2})\s+năm\s+(?P<year>\d{4})"
        )
        for line in self._lines(first_page):
            match = re.search(pattern, line, flags=re.IGNORECASE)
            if match:
                return self._clean_value(match.group("place"), 255), self._safe_date(
                    match.group("year"),
                    match.group("month"),
                    match.group("day"),
                )

        date_match = re.search(r"\b(?P<day>\d{1,2})[/-](?P<month>\d{1,2})[/-](?P<year>\d{4})\b", first_page)
        if date_match:
            return None, self._safe_date(date_match.group("year"), date_match.group("month"), date_match.group("day"))
        return None, None

    def _extract_title(self, first_page: str, document_type: str) -> str | None:
        label = DOCUMENT_TYPE_LABELS.get(document_type)
        if label and document_type != "UNKNOWN":
            words = label.split(" (", 1)[0].upper()
            for line in self._lines(first_page)[:25]:
                if words in line.upper():
                    return self._clean_value(line.upper(), 512)
        for line in self._lines(first_page)[:25]:
            if 5 <= len(line) <= 120 and line.isupper() and not line.startswith(("SỐ:", "CỘNG HÒA", "ĐỘC LẬP")):
                return self._clean_value(line, 512)
        return None

    def _extract_excerpt(self, first_page: str) -> str | None:
        match = re.search(r"\bV/v\s+([^\n]+(?:\n(?!K[íi]nh\s+g[ửu]i)[^\n]+)?)", first_page, flags=re.IGNORECASE)
        if match:
            return self._clean_value(" ".join(match.group(1).split()), 1000)

        lines = self._lines(first_page)
        for index, line in enumerate(lines[:35]):
            if re.search(r"^(về việc|về|triển khai|báo cáo|kế hoạch)\b", line, flags=re.IGNORECASE):
                return self._clean_value(line, 1000)
            if line.upper() in {"CÔNG VĂN", "THÔNG BÁO", "BÁO CÁO", "TỜ TRÌNH"} and index + 1 < len(lines):
                candidate = lines[index + 1]
                if not candidate.upper().startswith(("KÍNH GỬI", "SỐ:")):
                    return self._clean_value(candidate, 1000)
        return None

    def _extract_recipient(self, full_text: str) -> str | None:
        match = re.search(r"K[íi]nh\s+g[ửu]i\s*:?\s*([^\n]+(?:\n\s*[-+]\s*[^\n]+)*)", full_text, flags=re.IGNORECASE)
        if match:
            return self._clean_value(" ".join(match.group(1).split()), 1000)
        match = re.search(r"Nơi\s+nhận\s*:?\s*([^\n]+(?:\n\s*[-+]\s*[^\n]+)*)", full_text, flags=re.IGNORECASE)
        if match:
            return self._clean_value(" ".join(match.group(1).split()), 1000)
        return None

    def _extract_signer(self, full_text: str) -> tuple[str | None, str | None]:
        lines = self._lines(full_text)
        tail = lines[-25:]
        signer_name = None
        signer_title = None
        for line in reversed(tail):
            if re.search(r"^(Nơi nhận|Lưu|Ký bởi|Ngày ký)\b", line, flags=re.IGNORECASE):
                continue
            if self._looks_like_person_name(line):
                signer_name = self._clean_value(line, 255)
                break
        for line in tail:
            if re.search(r"\b(GIÁM ĐỐC|PHÓ GIÁM ĐỐC|TRƯỞNG PHÒNG|CHỦ TỊCH|PHÓ CHỦ TỊCH|KT\.|TL\.)\b", line.upper()):
                signer_title = self._clean_value(line, 255)
        return signer_title, signer_name

    def _detect_seal(self, full_text: str) -> bool | None:
        if re.search(r"\b(đã ký|ký bởi|chữ ký số|dấu|đóng dấu|dấu treo|dấu giáp lai)\b", full_text, flags=re.IGNORECASE):
            return True
        return None

    def _detect_attachment(self, full_text: str) -> bool:
        return bool(re.search(r"\b(phụ lục|kèm theo|attachment|tệp đính kèm)\b", full_text, flags=re.IGNORECASE))

    def _safe_date(self, year: str, month: str, day: str) -> date | None:
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            return None

    def _lines(self, text: str) -> list[str]:
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _clean_value(self, value: str | None, max_length: int) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip(" .;,:").split())
        return normalized[:max_length] or None

    def _looks_like_date_place(self, line: str) -> bool:
        return bool(re.search(r"\bngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}\b", line, flags=re.IGNORECASE))

    def _looks_like_person_name(self, line: str) -> bool:
        if not 5 <= len(line) <= 80:
            return False
        if re.search(r"\d|:|/|,|;", line):
            return False
        words = line.split()
        if len(words) < 2 or len(words) > 6:
            return False
        return sum(1 for word in words if word[:1].isupper()) >= 2
