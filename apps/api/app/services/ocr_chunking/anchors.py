from __future__ import annotations

import re

GROUP_A_ANCHORS = (
    "Căn cứ",
    "Xét đề nghị",
    "QUYẾT ĐỊNH",
    "NGHỊ QUYẾT",
    "CHỈ THỊ",
    "QUY CHẾ",
    "QUY ĐỊNH",
    "Chương",
    "Mục",
    "Điều",
    "Khoản",
    "Điểm",
    "Nơi nhận",
    "TM.",
    "KT.",
    "GIÁM ĐỐC",
    "CHỦ TỊCH",
)

GROUP_B_ANCHORS = (
    "Kính gửi",
    "V/v",
    "Thực hiện",
    "Căn cứ",
    "Mục đích",
    "Yêu cầu",
    "Nội dung",
    "Nhiệm vụ",
    "Giải pháp",
    "Tiến độ",
    "Kinh phí",
    "Tổ chức thực hiện",
    "Kiến nghị",
    "Đề xuất",
    "Nơi nhận",
)

GROUP_C_ANCHORS = (
    "HỢP ĐỒNG",
    "Bên A",
    "Bên B",
    "Điều",
    "Hôm nay",
    "vào hồi",
    "Tại",
    "Thành phần",
    "Đại diện",
    "Nội dung",
    "Bàn giao",
    "Thanh toán",
    "Số lượng",
    "Đơn giá",
    "Thành tiền",
    "Biên bản được lập thành",
)

GROUP_D_ANCHORS_BY_TYPE = {
    "GUQ": ("Người ủy quyền", "Người được ủy quyền", "Nội dung ủy quyền", "Thời hạn"),
    "GM": ("Trân trọng kính mời", "Thời gian", "Địa điểm", "Nội dung", "Thành phần"),
    "GGT": ("Giới thiệu ông/bà", "Đến liên hệ", "Về việc"),
    "GNP": ("Họ và tên", "Đơn vị", "Nghỉ từ ngày", "Đến ngày", "Lý do"),
    "PC": ("Người nhận tiền", "Số tiền", "Lý do chi", "Kèm theo"),
}

ARTICLE_RE = re.compile(r"^\s*Điều\s+(?P<number>\d+[a-zA-Z]?)\s*[\.:]?\s*(?P<title>.*)", re.IGNORECASE)
CHAPTER_RE = re.compile(r"^\s*Chương\s+(?P<number>[IVXLCDM\d]+)\s*[\.:]?\s*(?P<title>.*)", re.IGNORECASE)
CLAUSE_RE = re.compile(r"^\s*(?:Khoản\s+)?(?P<number>\d+)\s*[\).]\s+(?P<title>.+)")
POINT_RE = re.compile(r"^\s*(?P<number>[a-zđ])\s*[\).]\s+(?P<title>.+)", re.IGNORECASE)
ROMAN_SECTION_RE = re.compile(r"^\s*(?P<number>[IVXLCDM]+)\s*[\).]\s+(?P<title>.+)")
SIGNATURE_RE = re.compile(r"\b(?:Nơi nhận|TM\.|KT\.|GIÁM ĐỐC|CHỦ TỊCH|NGƯỜI\s+KÝ|ĐẠI DIỆN)\b", re.IGNORECASE)
APPENDIX_RE = re.compile(r"\b(?:PHỤ\s+LỤC|KÈM\s+THEO|DANH\s+SÁCH\s+KÈM)\b", re.IGNORECASE)
TABLE_HINT_RE = re.compile(r"\b(?:STT|Số lượng|Đơn giá|Thành tiền|Bảng|Tổng cộng)\b|(?:\s{2,}\S+){2,}", re.IGNORECASE)
