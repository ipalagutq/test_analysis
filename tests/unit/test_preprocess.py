"""Scan preprocessing: magic-byte type check, limits, PDF rasterization, resizing (R7)."""

from io import BytesIO

import pytest
from PIL import Image

from scan_files import SAMPLES_DIR, make_jpeg, make_pdf, make_png
from test_analysis.config import get_settings
from test_analysis.extraction import (
    FileTooLarge,
    TooManyPages,
    UnsupportedMediaType,
    detect_mime,
    preprocess,
)
from test_analysis.extraction.preprocess import MAX_SIDE_PX

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _image_size(png: bytes) -> tuple[int, int]:
    with Image.open(BytesIO(png)) as image:
        assert image.format == "PNG"
        return image.size


@pytest.mark.parametrize(
    ("data", "mime"),
    [
        (b"%PDF-1.7 ...", "application/pdf"),
        (b"\xff\xd8\xff\xe0 ...", "image/jpeg"),
        (PNG_SIGNATURE + b"...", "image/png"),
        (b"GIF89a ...", None),
        (b"plain text renamed to scan.pdf", None),
        (b"", None),
    ],
)
def test_detect_mime_uses_magic_bytes(data: bytes, mime: str | None) -> None:
    assert detect_mime(data) == mime


def test_preprocess_pdf_returns_png_per_page() -> None:
    scan = preprocess(make_pdf(pages=2))

    assert scan.mime == "application/pdf"
    assert len(scan.pages) == 2
    assert all(page.startswith(PNG_SIGNATURE) for page in scan.pages)


def test_preprocess_pdf_renders_at_200_dpi_when_small() -> None:
    # 300×400 pt page at 200 dpi → 833×1111 px, below the 2000 px cap
    scan = preprocess(make_pdf(pages=1, width=300, height=400))

    width, height = _image_size(scan.pages[0])
    assert width == pytest.approx(300 * 200 / 72, abs=2)
    assert height == pytest.approx(400 * 200 / 72, abs=2)


def test_preprocess_pdf_large_page_is_capped_at_max_side() -> None:
    scan = preprocess(make_pdf(pages=1, width=1200, height=1600))

    assert max(_image_size(scan.pages[0])) <= MAX_SIDE_PX


@pytest.mark.parametrize(("builder", "mime"), [(make_jpeg, "image/jpeg"), (make_png, "image/png")])
def test_preprocess_large_image_is_resized_to_max_side(builder, mime: str) -> None:
    scan = preprocess(builder(width=3000, height=1500))

    assert scan.mime == mime
    assert len(scan.pages) == 1
    assert _image_size(scan.pages[0]) == (MAX_SIDE_PX, 1000)


def test_preprocess_small_image_keeps_size() -> None:
    scan = preprocess(make_jpeg(width=640, height=480))

    assert _image_size(scan.pages[0]) == (640, 480)


def test_preprocess_jpeg_applies_exif_rotation() -> None:
    exif = Image.Exif()
    exif[0x0112] = 6  # orientation: rotate 90° clockwise to display
    buffer = BytesIO()
    Image.new("RGB", (400, 200), "white").save(buffer, format="JPEG", exif=exif)

    scan = preprocess(buffer.getvalue())

    assert _image_size(scan.pages[0]) == (200, 400)


def test_preprocess_rgba_png_is_converted_to_rgb() -> None:
    buffer = BytesIO()
    Image.new("RGBA", (50, 50), (255, 0, 0, 128)).save(buffer, format="PNG")

    scan = preprocess(buffer.getvalue())

    with Image.open(BytesIO(scan.pages[0])) as image:
        assert image.mode == "RGB"


def test_preprocess_text_file_is_unsupported() -> None:
    with pytest.raises(UnsupportedMediaType):
        preprocess(b"this is a .txt file renamed to .pdf")


@pytest.mark.parametrize(
    "data",
    [b"%PDF-1.7 truncated garbage", PNG_SIGNATURE + b"broken", b"\xff\xd8\xff broken"],
)
def test_preprocess_damaged_file_with_valid_signature_is_unsupported(data: bytes) -> None:
    with pytest.raises(UnsupportedMediaType):
        preprocess(data)


def test_preprocess_file_over_size_limit_is_rejected() -> None:
    data = make_png() + b"\0" * (1024 * 1024)

    with pytest.raises(FileTooLarge):
        preprocess(data, max_upload_mb=1)


def test_preprocess_size_limit_is_checked_before_type() -> None:
    with pytest.raises(FileTooLarge):
        preprocess(b"x" * (1024 * 1024 + 1), max_upload_mb=1)


def test_preprocess_pdf_at_page_limit_is_accepted() -> None:
    assert len(preprocess(make_pdf(pages=3), max_pdf_pages=3).pages) == 3


def test_preprocess_pdf_over_page_limit_is_rejected() -> None:
    with pytest.raises(TooManyPages, match="4 pages"):
        preprocess(make_pdf(pages=4), max_pdf_pages=3)


def test_preprocess_page_limit_defaults_to_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_PDF_PAGES", "1")
    get_settings.cache_clear()

    with pytest.raises(TooManyPages):
        preprocess(make_pdf(pages=2))


@pytest.mark.parametrize(
    ("name", "mime", "page_count"),
    [
        ("cbc_ivanova.pdf", "application/pdf", 2),
        ("biochem_petrov.jpg", "image/jpeg", 1),
        ("mixed_sidorova.png", "image/png", 1),
    ],
)
def test_preprocess_demo_samples(name: str, mime: str, page_count: int) -> None:
    scan = preprocess((SAMPLES_DIR / name).read_bytes())

    assert scan.mime == mime
    assert len(scan.pages) == page_count
    assert all(max(_image_size(page)) <= MAX_SIDE_PX for page in scan.pages)
