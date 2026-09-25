"""
validators.py — secure upload validation.

Three layers of defence before a file is accepted:
  1. Extension whitelist (fast, user-friendly)
  2. Size limit (protects bandwidth & storage quota)
  3. Magic-byte sniffing (catches "virus.exe renamed to notes.pdf")

In production you would additionally ship files to an AV scanner
(e.g. ClamAV lambda) before making them downloadable — see docs/security.md.
"""

import binascii


class FileValidationError(ValueError):
    """Raised when an uploaded file fails a validation rule."""


class FileSizeError(FileValidationError):
    """Oversized upload — mapped to HTTP 413 (Payload Too Large)."""


# Minimal magic-number table for the formats this portal allows.
MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    "pdf": [b"%PDF"],
    "zip": [b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"],
    # .docx / .pptx / .xlsx are ZIP containers (OOXML)
    "docx": [b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"],
    "pptx": [b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"],
    "xlsx": [b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"],
    "txt": [],                    # plain text: no reliable signature
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "png": [b"\x89PNG\r\n\x1a\n"],
}

# map common aliases onto canonical keys
_ALIASES = {"jpeg": "jpg", "doc": "docx"}


def normalize_extension(filename: str) -> str:
    """Return lowercase extension without the dot ('notes.PDF' -> 'pdf')."""
    if "." not in filename:
        return ""
    ext = filename.rsplit(".", 1)[1].strip().lower()
    return _ALIASES.get(ext, ext)


def validate_file(
    filename: str,
    data: bytes,
    allowed_extensions: list[str],
    max_size_mb: int,
) -> str:
    """
    Validate an upload. Returns the normalized extension on success.

    Raises FileValidationError with a user-friendly message otherwise.
    """
    # ---- 1. Extension whitelist ----
    ext = normalize_extension(filename)
    allowed = [normalize_extension(f"*.{e}") for e in allowed_extensions]
    if not ext:
        raise FileValidationError("File has no extension")
    if ext not in allowed:
        raise FileValidationError(
            f"File type '.{ext}' not allowed. Allowed: {', '.join('.' + a for a in allowed)}"
        )

    # ---- 2. Size limit (checked BEFORE touching storage) ----
    max_bytes = max_size_mb * 1024 * 1024
    if len(data) == 0:
        raise FileValidationError("File is empty")
    if len(data) > max_bytes:
        raise FileSizeError(
            f"File too large ({len(data) / (1024 * 1024):.1f} MB). Limit is {max_size_mb} MB"
        )

    # ---- 3. Magic-byte sniffing (content must match the extension) ----
    signatures = MAGIC_SIGNATURES.get(ext)
    if signatures:  # empty list = format with no fixed signature (e.g. txt)
        if not any(data.startswith(sig) for sig in signatures):
            raise FileValidationError(
                f"File content does not look like a real .{ext} file"
            )

    return ext


def validate_marks(marks: int, max_marks: int) -> None:
    """Grading rule: 0 <= marks <= assignment.max_marks."""
    if marks is None:
        raise ValueError("Marks are required")
    if marks < 0:
        raise ValueError("Marks cannot be negative")
    if marks > max_marks:
        raise ValueError(f"Marks ({marks}) exceed maximum ({max_marks})")


def is_safe_redirect_target(storage_path: str) -> bool:
    """Basic sanity check for object keys coming from untrusted places."""
    return ".." not in storage_path and storage_path.startswith("submissions/")
