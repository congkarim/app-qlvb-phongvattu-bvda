from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.services.document_content_service import DocumentContentService


VIETNAMESE_ACCENT_CHARS = set(
    "ăâđêôơưáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩị"
    "óòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"
    "ĂÂĐÊÔƠƯÁÀẢÃẠẮẰẲẴẶẤẦẨẪẬÉÈẺẼẸẾỀỂỄỆÍÌỈĨỊ"
    "ÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴ"
)
BENCHMARK_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".pdf"}
SAMPLE_TEXT = "\n".join(
    [
        "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
        "Độc lập - Tự do - Hạnh phúc",
        "Điều 1. Phạm vi điều chỉnh đấu thầu",
        "Khoản 1. Văn bản scan phải giữ dấu tiếng Việt.",
        "Số 74/VBHN-VPQH ngày 15 tháng 5 năm 2025.",
    ]
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=Path("/app/tests/fixtures/ocr_vi"))
    parser.add_argument("--engine", choices=["paddleocr", "paddle_vietocr", "all"], default="all")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--generate-sample", action="store_true")
    parser.add_argument("--files", nargs="*", help="Only benchmark the listed fixture filenames.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of fixture files to benchmark.")
    args = parser.parse_args()

    if args.generate_sample:
        generate_sample_fixture(args.fixtures)

    engines = ["paddleocr", "paddle_vietocr"] if args.engine == "all" else [args.engine]
    rows = []
    fixture_paths = list(iter_fixture_paths(args.fixtures, args.files, args.limit))
    for fixture_path in fixture_paths:
        truth_path = fixture_path.with_suffix(".txt")
        truth = truth_path.read_text(encoding="utf-8")
        for engine in engines:
            rows.append(run_benchmark(fixture_path, truth, engine))

    if args.format == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_markdown(rows)


def iter_fixture_paths(fixtures: Path, files: list[str] | None, limit: int | None):
    selected_names = set(files or [])
    count = 0
    for fixture_path in sorted(fixtures.iterdir()):
        if fixture_path.suffix.lower() not in BENCHMARK_SUFFIXES:
            continue
        if not fixture_path.with_suffix(".txt").exists():
            continue
        if selected_names and fixture_path.name not in selected_names:
            continue
        yield fixture_path
        count += 1
        if limit is not None and count >= limit:
            break


def run_benchmark(fixture_path: Path, truth: str, engine: str) -> dict[str, object]:
    service = DocumentContentService()
    service.settings = service.settings.model_copy(update={"ocr_engine": engine})
    start = time.perf_counter()
    error = ""
    text = ""
    confidence = 0.0
    page_count = 0
    try:
        pages = service.extract_pages(fixture_path, fixture_path.name)
        page_count = len(pages)
        text = "\n".join(page.text for page in pages)
        confidence = round(sum(page.confidence for page in pages) / max(page_count, 1), 4)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    runtime = time.perf_counter() - start
    return {
        "file": fixture_path.name,
        "engine": engine,
        "pages": page_count,
        "confidence": confidence,
        "cer": character_error_rate(truth, text) if not error else None,
        "wer": word_error_rate(truth, text) if not error else None,
        "accent_loss_rate": accent_loss_rate(truth, text) if not error else None,
        "runtime_seconds": round(runtime, 3),
        "seconds_per_page": round(runtime / max(page_count, 1), 3),
        "error": error,
        "text": text,
    }


def character_error_rate(truth: str, predicted: str) -> float:
    truth_norm = normalize_for_metric(truth)
    predicted_norm = normalize_for_metric(predicted)
    if not truth_norm:
        return 0.0
    return round(edit_distance(truth_norm, predicted_norm) / len(truth_norm), 4)


def word_error_rate(truth: str, predicted: str) -> float:
    truth_words = normalize_for_metric(truth).split()
    predicted_words = normalize_for_metric(predicted).split()
    if not truth_words:
        return 0.0
    return round(edit_distance(truth_words, predicted_words) / len(truth_words), 4)


def accent_loss_rate(truth: str, predicted: str) -> float:
    truth_accent_count = sum(1 for char in truth if char in VIETNAMESE_ACCENT_CHARS)
    predicted_accent_count = sum(1 for char in predicted if char in VIETNAMESE_ACCENT_CHARS)
    if truth_accent_count == 0:
        return 0.0
    lost = max(truth_accent_count - predicted_accent_count, 0)
    return round(lost / truth_accent_count, 4)


def normalize_for_metric(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def edit_distance(left, right) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_value in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_value in enumerate(right, start=1):
            insertion = current[right_index - 1] + 1
            deletion = previous[right_index] + 1
            substitution = previous[right_index - 1] + (left_value != right_value)
            current.append(min(insertion, deletion, substitution))
        previous = current
    return previous[-1]


def print_markdown(rows: list[dict[str, object]]) -> None:
    print("| file | engine | pages | confidence | CER | WER | accent loss | seconds | sec/page | error |")
    print("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in rows:
        print(
            "| {file} | {engine} | {pages} | {confidence} | {cer} | {wer} | {accent_loss_rate} | "
            "{runtime_seconds} | {seconds_per_page} | {error} |".format(**row)
        )


def generate_sample_fixture(fixtures: Path) -> None:
    fixtures.mkdir(parents=True, exist_ok=True)
    image_path = fixtures / "sample_001.png"
    text_path = fixtures / "sample_001.txt"
    text_path.write_text(SAMPLE_TEXT, encoding="utf-8")

    font_regular = find_font(bold=False)
    font_bold = find_font(bold=True)
    image = Image.new("RGB", (1900, 950), "white")
    draw = ImageDraw.Draw(image)
    normal = ImageFont.truetype(str(font_regular), 52) if font_regular else ImageFont.load_default()
    bold = ImageFont.truetype(str(font_bold or font_regular), 56) if font_regular or font_bold else normal
    y = 100
    for index, line in enumerate(SAMPLE_TEXT.splitlines()):
        font = bold if index == 0 else normal
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (image.width - (bbox[2] - bbox[0])) // 2 if index < 2 else 120
        draw.text((x, y), line, fill="black", font=font)
        y += 115
    image.filter(ImageFilter.GaussianBlur(radius=0.2)).save(image_path)


def find_font(bold: bool) -> Path | None:
    names = [
        "NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf",
    ]
    for root in [Path("/usr/share/fonts"), Path("/usr/local/share/fonts")]:
        for name in names:
            matches = list(root.rglob(name)) if root.exists() else []
            if matches:
                return matches[0]
    return None


if __name__ == "__main__":
    main()
