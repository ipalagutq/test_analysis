"""Scan file preparation: type check by magic bytes, limits, PDF rasterization, resizing."""

from io import BytesIO
from typing import Literal

import pypdfium2 as pdfium
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict

from test_analysis.config import get_settings

ScanMime = Literal["application/pdf", "image/jpeg", "image/png"]

PDF_DPI = 200
MAX_SIDE_PX = 2000

_MIME_BY_SIGNATURE: tuple[tuple[bytes, ScanMime], ...] = (
    (b"%PDF-", "application/pdf"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
)


# exception names are fixed by the spec (R7, stage 7 error mapping)
class UnsupportedMediaType(Exception):
    """The file is not a readable PDF, JPEG or PNG."""


class FileTooLarge(Exception):
    """The file exceeds `MAX_UPLOAD_MB`."""


class TooManyPages(Exception):
    """The PDF has more pages than `MAX_PDF_PAGES`."""


class ScanPages(BaseModel):
    """Original file type and its pages as PNG images, longest side ≤ 2000 px."""

    model_config = ConfigDict(frozen=True)

    mime: ScanMime
    pages: list[bytes]


def detect_mime(data: bytes) -> ScanMime | None:
    """Return the scan type by its leading magic bytes; `None` for anything else."""
    for signature, mime in _MIME_BY_SIGNATURE:
        if data.startswith(signature):
            return mime
    return None


def preprocess(
    data: bytes, *, max_upload_mb: int | None = None, max_pdf_pages: int | None = None
) -> ScanPages:
    """Validate an uploaded scan and turn it into PNG pages ready for the vision-LLM."""
    settings = get_settings()
    max_upload_mb = max_upload_mb or settings.max_upload_mb
    max_pdf_pages = max_pdf_pages or settings.max_pdf_pages

    if len(data) > max_upload_mb * 1024 * 1024:
        raise FileTooLarge(f"file is larger than {max_upload_mb} MB")
    mime = detect_mime(data)
    if mime is None:
        raise UnsupportedMediaType("only PDF, JPEG and PNG files are accepted")

    if mime == "application/pdf":
        images = _rasterize_pdf(data, max_pdf_pages)
    else:
        images = [_open_image(data)]
    return ScanPages(mime=mime, pages=[_to_png(image) for image in images])


def _rasterize_pdf(data: bytes, max_pages: int) -> list[Image.Image]:
    try:
        document = pdfium.PdfDocument(data)
    except pdfium.PdfiumError as error:
        raise UnsupportedMediaType("PDF file cannot be read") from error
    try:
        page_count = len(document)
        if page_count == 0:
            raise UnsupportedMediaType("PDF file has no pages")
        if page_count > max_pages:
            raise TooManyPages(f"PDF has {page_count} pages, at most {max_pages} are accepted")
        images = []
        for page in document:
            width, height = page.get_size()
            # render straight to the final size instead of a full 200 dpi bitmap
            scale = min(PDF_DPI / 72, MAX_SIDE_PX / max(width, height))
            images.append(page.render(scale=scale).to_pil())
            page.close()
        return images
    finally:
        document.close()


def _open_image(data: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(data))
        image.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as error:
        raise UnsupportedMediaType("image file cannot be read") from error
    return ImageOps.exif_transpose(image)


def _to_png(image: Image.Image) -> bytes:
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    image.thumbnail((MAX_SIDE_PX, MAX_SIDE_PX))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
