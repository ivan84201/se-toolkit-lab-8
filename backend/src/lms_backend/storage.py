"""Physical file storage on the filesystem."""

import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

# Root directory for stored files
STORAGE_ROOT = Path("files")


def _ensure_user_dir(user_id: int) -> Path:
    """Ensure the user's subdirectory exists. Create it if missing."""
    user_dir = STORAGE_ROOT / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def resolve_file_path(user_id: int, filename: str) -> Path:
    """Return the full filesystem path for a file belonging to a user."""
    return STORAGE_ROOT / str(user_id) / filename


def save_file(user_id: int, filename: str, content: bytes) -> str:
    """Save file content to the filesystem.

    Returns the relative path (e.g. 'files/123/myfile.pdf').
    Raises FileExistsError (409) if a file with the same name already exists.
    Raises OSError (500) on disk write failure.
    """
    user_dir = _ensure_user_dir(user_id)
    dest = user_dir / filename

    if dest.exists():
        raise FileExistsError(f"File already exists: {dest}")

    dest.write_bytes(content)
    logger.info(
        "file_saved",
        extra={
            "event": "file_saved",
            "user_id": user_id,
            "path": str(dest),
        },
    )
    # Return path relative to STORAGE_ROOT (e.g. '123/myfile.pdf')
    return str(dest.relative_to(STORAGE_ROOT))


def delete_file(relative_path: str) -> None:
    """Delete a file from the filesystem.

    Raises FileNotFoundError if the file does not exist (not an error).
    Raises OSError (500) on disk deletion failure.
    """
    full_path = STORAGE_ROOT / relative_path
    if not full_path.exists():
        logger.warning(
            "file_not_found_on_delete",
            extra={"event": "file_not_found_on_delete", "path": str(full_path)},
        )
        return

    full_path.unlink()
    logger.info(
        "file_deleted",
        extra={
            "event": "file_deleted",
            "path": str(full_path),
        },
    )


def file_exists(relative_path: str) -> bool:
    """Check if a file exists on the filesystem."""
    return (STORAGE_ROOT / relative_path).is_file()


def get_file_size(relative_path: str) -> int:
    """Return file size in bytes, or -1 if not found."""
    full_path = STORAGE_ROOT / relative_path
    if full_path.is_file():
        return full_path.stat().st_size
    return -1
