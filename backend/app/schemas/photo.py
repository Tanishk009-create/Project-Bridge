import base64
import re

from fastapi import HTTPException

PHOTO_PATTERN = re.compile(r"^data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/]+={0,2})$")


def validate_photo(value: str | None) -> str | None:
    if value is None:
        return None
    match = PHOTO_PATTERN.fullmatch(value)
    if not match:
        raise ValueError("Choose a JPEG, PNG or WebP photo.")
    try:
        decoded = base64.b64decode(match.group(2), validate=True)
    except (ValueError, base64.binascii.Error):
        raise ValueError("The photo could not be read.") from None
    if len(decoded) > 750_000:
        raise ValueError("Photo must be under 750 KB after resizing.")
    signatures = {"image/jpeg": decoded.startswith(b"\xff\xd8\xff"),
                  "image/png": decoded.startswith(b"\x89PNG\r\n\x1a\n"),
                  "image/webp": decoded.startswith(b"RIFF") and decoded[8:12] == b"WEBP"}
    if not signatures[match.group(1)]:
        raise ValueError("The photo format does not match its contents.")
    return value
