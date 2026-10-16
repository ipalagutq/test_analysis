"""Builders of small synthetic scan files for preprocessing and upload tests."""

from io import BytesIO
from pathlib import Path

from PIL import Image

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "data" / "samples"


def make_png(width: int = 400, height: int = 300) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def make_jpeg(width: int = 400, height: int = 300) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), "white").save(buffer, format="JPEG")
    return buffer.getvalue()


def make_pdf(pages: int, width: int = 600, height: int = 800) -> bytes:
    images = [Image.new("RGB", (width, height), "white") for _ in range(pages)]
    buffer = BytesIO()
    images[0].save(buffer, format="PDF", save_all=True, append_images=images[1:], resolution=72)
    return buffer.getvalue()
