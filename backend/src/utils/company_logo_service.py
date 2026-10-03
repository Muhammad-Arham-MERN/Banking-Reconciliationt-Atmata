# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Company logo storage.

Logos live in COMPANY_LOGO_DIR — deliberately OUTSIDE UPLOAD_DIR. The
reconciliation file lifecycle deletes everything in UPLOAD_DIR (a 20-minute
retention sweep on startup and a full wipe on shutdown), so a logo stored
there would be silently erased. This module owns the persistent location.

Only PNG, JPG/JPEG and SVG are accepted. No size cap is imposed by this
feature (a Developer decision), so uploads are streamed to disk in chunks
rather than buffered whole in memory.
"""
import logging
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import UploadFile

from src.config import settings

logger = logging.getLogger(__name__)

# Extension -> canonical content type. The extension is the single source of
# truth for both the stored filename and the Content-Type used when serving.
ALLOWED_LOGO_TYPES: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
}

CHUNK_SIZE = 64 * 1024

# Magic-byte signatures for the binary formats. SVG is text and is sniffed
# separately (it has no binary signature).
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_JPEG_SIGNATURE = b"\xff\xd8\xff"


class UnsupportedLogoTypeError(Exception):
    """Raised when an uploaded logo is not a PNG, JPG, or SVG."""


def _extension_for(original_filename: str) -> str:
    suffix = Path(original_filename or "").suffix.lower()
    if suffix not in ALLOWED_LOGO_TYPES:
        raise UnsupportedLogoTypeError(
            "Only PNG, JPG, or SVG logo files are accepted."
        )
    return suffix


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _assert_signature(head: bytes, extension: str) -> None:
    """Verify the leading bytes match the declared extension.

    Extension alone is not enough — a renamed file must not slip through and be
    served later with an image content type it does not deserve.
    """
    if extension == ".png":
        if not head.startswith(_PNG_SIGNATURE):
            raise UnsupportedLogoTypeError("File is not a valid PNG image.")
        return
    if extension in (".jpg", ".jpeg"):
        if not head.startswith(_JPEG_SIGNATURE):
            raise UnsupportedLogoTypeError("File is not a valid JPG image.")
        return
    # SVG: XML text containing an <svg> element.
    try:
        text = head.decode("utf-8", errors="ignore").lstrip()
    except Exception:  # pragma: no cover - decode never raises with errors=ignore
        raise UnsupportedLogoTypeError("File is not a valid SVG image.")
    lowered = text.lower()
    if "<?xml" in lowered:
        lowered = lowered.split("?>", 1)[-1].lstrip()
    if not lowered.startswith("<svg") and "<svg" not in lowered:
        raise UnsupportedLogoTypeError("File is not a valid SVG image.")


def logo_path(filename: str) -> Path:
    """Absolute path for a stored logo filename.

    Rejects anything that is not a bare filename so a stored value can never
    be used to escape the logo directory.
    """
    if not filename or filename != Path(filename).name:
        raise ValueError("Invalid logo filename")
    return settings.COMPANY_LOGO_DIR / filename


def logo_content_type(filename: str) -> str:
    """Content type to serve a stored logo with (falls back to PNG's type)."""
    return ALLOWED_LOGO_TYPES.get(Path(filename).suffix.lower(), "application/octet-stream")


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
async def save_logo(upload: UploadFile) -> str:
    """Stream an uploaded logo to COMPANY_LOGO_DIR under a generated name.

    The client-supplied name is never used for storage — only its extension is
    trusted (and then verified against the file's actual signature). Returns the
    generated filename to persist in the companies row.
    """
    extension = _extension_for(upload.filename or "")
    filename = f"{uuid4().hex}{extension}"
    destination = logo_path(filename)

    settings.COMPANY_LOGO_DIR.mkdir(parents=True, exist_ok=True)

    wrote_any = False
    try:
        async with aiofiles.open(destination, "wb") as handle:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break
                if not wrote_any:
                    # Validate against the head of the file before writing more.
                    _assert_signature(chunk, extension)
                wrote_any = True
                await handle.write(chunk)
    except Exception:
        # Never leave a partial or invalid file behind.
        destination.unlink(missing_ok=True)
        raise

    if not wrote_any:
        destination.unlink(missing_ok=True)
        raise UnsupportedLogoTypeError("The uploaded logo file is empty.")

    logger.info("Stored company logo: %s", filename)
    return filename


def delete_logo(filename: str | None) -> bool:
    """Best-effort delete of a stored logo. Never raises."""
    if not filename:
        return False
    try:
        logo_path(filename).unlink(missing_ok=True)
        return True
    except Exception as exc:
        logger.warning("Could not delete company logo %s: %s", filename, exc)
        return False

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
