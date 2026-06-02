from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


FIXTURE_DIR = Path(__file__).resolve().parent
PAGE_SIZE = (1200, 1600)
MARGIN_X = 90


FIXTURES = {
    "sample_001": {
        "kind": "clear",
        "lines": [
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
            "Độc lập - Tự do - Hạnh phúc",
            "Điều 1. Phạm vi điều chỉnh đấu thầu",
            "Khoản 1. Văn bản scan phải giữ dấu tiếng Việt.",
            "Số 74/VBHN-VPQH ngày 15 tháng 5 năm 2025.",
        ],
    },
    "sample_002": {
        "kind": "clear",
        "lines": [
            "ỦY BAN NHÂN DÂN TỈNH MINH HẢI",
            "Số: 12/2026/QĐ-UBND",
            "QUYẾT ĐỊNH",
            "Về việc ban hành quy chế quản lý vật tư dự phòng",
            "Điều 1. Ban hành kèm theo Quyết định này Quy chế quản lý vật tư dự phòng.",
            "Điều 2. Các đơn vị sử dụng vật tư phải cập nhật sổ theo dõi hằng tháng.",
            "Điều 3. Quyết định này có hiệu lực từ ngày 01 tháng 7 năm 2026.",
        ],
    },
    "sample_003": {
        "kind": "compressed",
        "lines": [
            "BỘ TÀI CHÍNH",
            "Số: 45/2026/TT-BTC",
            "THÔNG TƯ",
            "Hướng dẫn lập dự toán mua sắm vật tư phục vụ sản xuất",
            "Khoản 1. Hồ sơ đề nghị mua sắm phải nêu rõ chủng loại, số lượng và đơn giá.",
            "Khoản 2. Đơn vị thẩm định chịu trách nhiệm kiểm tra nguồn vốn trước khi trình duyệt.",
            "Ngày ban hành: 18 tháng 4 năm 2026.",
        ],
    },
    "sample_004": {
        "kind": "two_column",
        "left_lines": [
            "Điều 5. Kiểm kê vật tư",
            "1. Kho vật tư thực hiện kiểm kê định kỳ vào ngày cuối quý.",
            "2. Biên bản kiểm kê phải có chữ ký của thủ kho và kế toán.",
            "3. Vật tư hư hỏng được lập danh sách riêng để xử lý.",
        ],
        "right_lines": [
            "Điều 6. Báo cáo sử dụng",
            "1. Báo cáo gửi về phòng vật tư trước ngày 05 hằng tháng.",
            "2. Số liệu báo cáo phải khớp với phiếu xuất, phiếu nhập.",
            "Ghi chú: Không tự ý điều chuyển vật tư giữa các công trình.",
        ],
    },
    "sample_005": {
        "kind": "skewed",
        "lines": [
            "CÔNG TY ĐIỆN LỰC KHU VỰC III",
            "BIÊN BẢN BÀN GIAO VẬT TƯ",
            "Số hiệu: BB-09/VT-2026",
            "Ngày 22 tháng 3 năm 2026, hai bên tiến hành bàn giao vật tư theo danh mục.",
            "Điều 1. Bên nhận chịu trách nhiệm bảo quản vật tư sau khi ký biên bản.",
            "Điều 2. Mọi chênh lệch phải được lập phụ lục trong vòng 03 ngày làm việc.",
        ],
    },
    "sample_006": {
        "kind": "pdf",
        "pages": [
            [
                "TỔNG CÔNG TY HẠ TẦNG KỸ THUẬT",
                "KẾ HOẠCH MUA SẮM VẬT TƯ NĂM 2026",
                "Số: 08/KH-HTKT",
                "Mục I. Phạm vi kế hoạch",
                "Kế hoạch áp dụng cho vật tư phục vụ sửa chữa thường xuyên.",
                "Danh mục ưu tiên gồm cáp điện, thiết bị đóng cắt và vật tư an toàn.",
            ],
            [
                "Mục II. Tổ chức thực hiện",
                "Phòng vật tư tổng hợp nhu cầu trước ngày 20 tháng 6 năm 2026.",
                "Bộ phận tài chính rà soát nguồn vốn trước khi phát hành hồ sơ.",
                "Điều 4. Các đơn vị chịu trách nhiệm về tính chính xác của số liệu đề xuất.",
                "Kế hoạch này có hiệu lực kể từ ngày ký.",
            ],
        ],
    },
}


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for name, config in FIXTURES.items():
        if config["kind"] == "pdf":
            write_pdf_fixture(name, config["pages"])
            continue

        if config["kind"] == "two_column":
            image = render_two_column(config["left_lines"], config["right_lines"])
            truth_lines = [*config["left_lines"], *config["right_lines"]]
        else:
            image = render_single_column(config["lines"])
            truth_lines = config["lines"]

        image = degrade_image(image, config["kind"], seed=sum(ord(char) for char in name))
        image.save(FIXTURE_DIR / f"{name}.png")
        write_truth(name, truth_lines)


def write_pdf_fixture(name: str, pages: list[list[str]]) -> None:
    rendered_pages = [render_single_column(lines) for lines in pages]
    rendered_pages[0].save(FIXTURE_DIR / f"{name}.pdf", save_all=True, append_images=rendered_pages[1:])
    truth_lines: list[str] = []
    for index, lines in enumerate(pages, start=1):
        if index > 1:
            truth_lines.append("")
        truth_lines.extend(lines)
    write_truth(name, truth_lines)


def render_single_column(lines: list[str]) -> Image.Image:
    image = Image.new("RGB", PAGE_SIZE, "white")
    draw = ImageDraw.Draw(image)
    regular = load_font(size=31, bold=False)
    bold = load_font(size=36, bold=True)
    title = load_font(size=39, bold=True)
    y = 120

    for index, line in enumerate(lines):
        font = title if index == 0 else bold if index in {1, 2} else regular
        text_width = draw.textbbox((0, 0), line, font=font)[2]
        centered = index < 3 or line.isupper()
        x = (PAGE_SIZE[0] - text_width) // 2 if centered else MARGIN_X
        draw.text((x, y), line, fill=(20, 20, 20), font=font)
        y += 68 if index < 3 else 58

    return image


def render_two_column(left_lines: list[str], right_lines: list[str]) -> Image.Image:
    image = Image.new("RGB", PAGE_SIZE, "white")
    draw = ImageDraw.Draw(image)
    regular = load_font(size=26, bold=False)
    bold = load_font(size=30, bold=True)
    draw.text((MARGIN_X, 85), "PHỤ LỤC QUY TRÌNH KIỂM SOÁT VẬT TƯ", fill=(20, 20, 20), font=bold)
    draw.line((MARGIN_X, 150, PAGE_SIZE[0] - MARGIN_X, 150), fill=(80, 80, 80), width=2)
    draw_column(draw, left_lines, x=MARGIN_X, y=195, width=470, regular=regular, bold=bold)
    draw_column(draw, right_lines, x=640, y=195, width=460, regular=regular, bold=bold)
    draw.line((590, 180, 590, 640), fill=(160, 160, 160), width=1)
    return image


def draw_column(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    x: int,
    y: int,
    width: int,
    regular: ImageFont.FreeTypeFont,
    bold: ImageFont.FreeTypeFont,
) -> None:
    current_y = y
    for index, line in enumerate(lines):
        font = bold if index == 0 else regular
        for wrapped in wrap_text(draw, line, font, width):
            draw.text((x, current_y), wrapped, fill=(20, 20, 20), font=font)
            current_y += 50
        current_y += 14


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def degrade_image(image: Image.Image, kind: str, seed: int) -> Image.Image:
    if kind == "clear":
        return image.filter(ImageFilter.GaussianBlur(radius=0.15))
    if kind == "compressed":
        small = image.resize((790, 1053), Image.Resampling.BILINEAR)
        return small.resize(PAGE_SIZE, Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(radius=1.0))
    if kind == "skewed":
        noisy = add_noise(image, seed=seed, amount=1000)
        return noisy.rotate(1.2, resample=Image.Resampling.BICUBIC, expand=False, fillcolor="white")
    if kind == "two_column":
        return add_noise(image.filter(ImageFilter.GaussianBlur(radius=0.35)), seed=seed, amount=450)
    return image


def add_noise(image: Image.Image, seed: int, amount: int) -> Image.Image:
    random.seed(seed)
    noisy = image.copy()
    draw = ImageDraw.Draw(noisy)
    for _ in range(amount):
        x = random.randrange(0, image.width)
        y = random.randrange(0, image.height)
        shade = random.randrange(120, 230)
        draw.point((x, y), fill=(shade, shade, shade))
    return noisy


def write_truth(name: str, lines: list[str]) -> None:
    (FIXTURE_DIR / f"{name}.txt").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def load_font(size: int, bold: bool) -> ImageFont.FreeTypeFont:
    font_path = find_font(bold=bold)
    if font_path:
        return ImageFont.truetype(str(font_path), size)
    return ImageFont.load_default()


def find_font(bold: bool) -> Path | None:
    names = [
        "NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf",
    ]
    for root in [Path("/usr/share/fonts"), Path("/usr/local/share/fonts")]:
        if not root.exists():
            continue
        for name in names:
            matches = list(root.rglob(name))
            if matches:
                return matches[0]
    return None


if __name__ == "__main__":
    main()
