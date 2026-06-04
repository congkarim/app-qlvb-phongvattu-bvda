from dataclasses import dataclass

from app.services.document_classifier_service import DocumentClassifierService


@dataclass(frozen=True)
class TextPage:
    text: str


def _page(text: str) -> TextPage:
    return TextPage(text=text)


def main() -> None:
    service = DocumentClassifierService()
    cases = [
        (
            "CV",
            """
            BỆNH VIỆN ĐA KHOA MINH PHÚ
            Số: 123/CV-BV
            Hà Nội, ngày 04 tháng 06 năm 2026
            CÔNG VĂN
            V/v đề nghị cung cấp vật tư y tế
            Kính gửi: Phòng Vật tư
            GIÁM ĐỐC
            Nguyễn Văn A
            """,
            {
                "document_number": "123/CV-BV",
                "symbol": "CV-BV",
                "place": "Hà Nội",
                "date": "2026-06-04",
                "excerpt": "đề nghị cung cấp vật tư y tế",
                "recipient": "Phòng Vật tư",
            },
        ),
        (
            "QĐ",
            """
            ỦY BAN NHÂN DÂN TỈNH A
            Số: 01/QĐ-UBND
            Hà Nội, ngày 01 tháng 01 năm 2026
            QUYẾT ĐỊNH
            Về việc ban hành quy chế quản lý vật tư
            Điều 1. Ban hành kèm theo quyết định này.
            CHỦ TỊCH
            Trần Văn B
            """,
            {},
        ),
        (
            "TB",
            """
            PHÒNG VẬT TƯ
            THÔNG BÁO
            Về lịch kiểm kê kho vật tư
            """,
            {},
        ),
        (
            "BB",
            """
            BIÊN BẢN
            Họp kiểm tra tình trạng vật tư
            Thành phần tham dự: Phòng Vật tư, Phòng Kế toán
            """,
            {},
        ),
        (
            "GM",
            """
            GIẤY MỜI
            Kính gửi: Phòng Vật tư
            Trân trọng kính mời dự họp vào ngày 04 tháng 06 năm 2026.
            """,
            {},
        ),
        (
            "UNKNOWN",
            """
            Nội dung scan thiếu tiêu đề và không đủ thông tin nhận diện.
            """,
            {},
        ),
    ]

    for expected_type, text, expected_fields in cases:
        result = service.classify([_page(text)])
        assert result.document_type == expected_type, (expected_type, result)
        for field, expected_value in expected_fields.items():
            actual_value = getattr(result, field)
            if field == "date" and actual_value is not None:
                actual_value = actual_value.isoformat()
            assert actual_value == expected_value, (field, expected_value, actual_value, result)

    print("document classifier checks passed")


if __name__ == "__main__":
    main()
