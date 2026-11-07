"""Product photo processing and storage.

The real type is checked with Pillow (not the extension), every image is re-encoded to WebP
(this drops EXIF and anything hidden in the file), file names are uuid4 and paths are never built
from user input.
"""

import io
import shutil
import uuid
import warnings
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings
from app.services.errors import BadRequestError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_FILES_PER_REQUEST = 10
MAX_IMAGES_PER_PRODUCT = 30
ALLOWED_FORMATS = frozenset({"JPEG", "PNG", "WEBP"})
FULL_SIZE = 1600
THUMB_SIZE = 400
WEBP_QUALITY = 85

# Decompression bomb protection: 40 megapixels, and Pillow's warning is treated as an error
Image.MAX_IMAGE_PIXELS = 40_000_000

MEDIA_URL_PREFIX = "/media/"
THUMB_SUFFIX = "_400"


@dataclass(frozen=True, slots=True)
class ProcessedImage:
    full: bytes
    thumb: bytes


def _encode(image: Image.Image, max_side: int) -> bytes:
    copy = image.copy()
    copy.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    copy.save(buffer, format="WEBP", quality=WEBP_QUALITY, method=4)
    return buffer.getvalue()


def process_image(data: bytes) -> ProcessedImage:
    """Validate and re-encode one uploaded image. CPU-bound: run it in a thread."""
    invalid = BadRequestError("Unsupported image. Allowed formats: JPEG, PNG, WebP")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as probe:
                if probe.format not in ALLOWED_FORMATS:
                    raise invalid
                probe.verify()  # structural check; the image must be reopened afterwards
            with Image.open(io.BytesIO(data)) as source:
                source.load()
                image = ImageOps.exif_transpose(source)
                has_alpha = image.mode in ("RGBA", "LA") or (
                    image.mode == "P" and "transparency" in image.info
                )
                image = image.convert("RGBA" if has_alpha else "RGB")
                return ProcessedImage(
                    full=_encode(image, FULL_SIZE), thumb=_encode(image, THUMB_SIZE)
                )
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise BadRequestError("Image is too large (maximum 40 megapixels)") from None
    except BadRequestError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise invalid from None


def product_dir(product_id: int) -> Path:
    return settings.MEDIA_DIR / "products" / str(int(product_id))


def new_file_path(product_id: int) -> str:
    """Relative path stored in product_images.file_path, e.g. products/7/<uuid>.webp"""
    return f"products/{int(product_id)}/{uuid.uuid4().hex}.webp"


def thumb_path(file_path: str) -> str:
    return file_path.removesuffix(".webp") + f"{THUMB_SUFFIX}.webp"


def file_url(file_path: str) -> str:
    return MEDIA_URL_PREFIX + file_path


def thumb_url(file_path: str) -> str:
    return MEDIA_URL_PREFIX + thumb_path(file_path)


def _absolute(file_path: str) -> Path:
    path = (settings.MEDIA_DIR / file_path).resolve()
    if not path.is_relative_to(settings.MEDIA_DIR):
        raise ValueError("Path outside of MEDIA_DIR")
    return path


def write_image(file_path: str, image: ProcessedImage) -> None:
    full = _absolute(file_path)
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_bytes(image.full)
    _absolute(thumb_path(file_path)).write_bytes(image.thumb)


def delete_image_files(file_path: str) -> None:
    for path in (file_path, thumb_path(file_path)):
        _absolute(path).unlink(missing_ok=True)


def delete_product_dir(product_id: int) -> None:
    shutil.rmtree(product_dir(product_id), ignore_errors=True)
