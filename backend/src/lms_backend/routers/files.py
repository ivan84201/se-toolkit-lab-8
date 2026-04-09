"""Router for file endpoints."""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.database import get_session
from lms_backend.db.files import (
    add_file,
    add_tags,
    find_files_by_tag,
    find_id_by_name,
    get_all_user_tags,
    get_file_tags,
    get_user_files,
    remove_file,
    remove_tags,
)
from lms_backend.models.file import FileRead, FileRecord
from lms_backend.models.user import UserRecord
from lms_backend.storage import STORAGE_ROOT

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=FileRead, status_code=201)
async def post_file(
    file: UploadFile,
    user_id: int,
    tags: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Upload a file. Stores to filesystem (files/<user_id>/) and creates DB record.

    - `file`: The file to upload (multipart form data)
    - `user_id`: Telegram user identifier (auto-created if missing)
    - `tags`: Optional comma-separated tags (e.g. "python,tutorial,draft")
    """
    # Auto-create user if they don't exist yet
    existing = await session.exec(select(UserRecord).where(UserRecord.id == user_id))
    if existing.first() is None:
        session.add(UserRecord(id=user_id, username=""))
        await session.commit()

    content = await file.read()
    filename = file.filename or "unnamed"
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    try:
        return await add_file(session, user_id, filename, content, tag_list)
    except FileExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"File '{filename}' already exists for user {user_id}",
        )
    except OSError as exc:
        logger.error(
            "file_save_disk_error",
            extra={"event": "file_save_disk_error", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file to disk: {exc}",
        ) from exc
    except Exception as exc:
        logger.error(
            "file_create_failed",
            extra={"event": "file_create_failed", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database service unavailable",
        ) from exc


@router.get("/user/{user_id}", response_model=list[FileRead])
async def get_files(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Show all files for a user."""
    return await get_user_files(session, user_id)


@router.get("/user/{user_id}/find")
async def find_file_by_name(
    user_id: int,
    filename: str,
    session: AsyncSession = Depends(get_session),
):
    """Find a file ID by filename for a user."""
    file_id = await find_id_by_name(session, user_id, filename)
    if file_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filename}' not found for user {user_id}",
        )
    return {"file_id": file_id, "filename": filename}


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove a file from filesystem and database. Related file_tags auto-delete via CASCADE."""
    file_record = await session.get(FileRecord, file_id)
    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    if file_record.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this file",
        )
    try:
        deleted = await remove_file(session, file_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )
    except OSError as exc:
        logger.error(
            "file_delete_disk_error",
            extra={"event": "file_delete_disk_error", "file_id": file_id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file from disk: {exc}",
        )
    return None


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Download a file by its ID. Returns the actual file from disk."""
    file_record = await session.get(FileRecord, file_id)
    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    file_path = Path(STORAGE_ROOT) / file_record.file_path
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )


@router.get("/{file_id}/tags", response_model=list[str])
async def get_tags_for_file(
    file_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Show all tags for a file."""
    tags = await get_file_tags(session, file_id)
    if not tags:
        file_exists = await session.get(FileRecord, file_id)
        if file_exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )
    return tags


@router.get("/{file_id}/content")
async def read_file_content(
    file_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Read text content of a file by ID. Returns text content (truncated to 8000 chars) and file metadata.

    Works best for text files (.py, .md, .txt, .json, etc.). Binary files return a warning.
    """
    file_record = await session.get(FileRecord, file_id)
    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    file_path = Path(STORAGE_ROOT) / file_record.file_path
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    # For large or binary files, just return metadata without reading content
    file_size = file_path.stat().st_size
    if file_size > 100_000:  # >100KB, skip content reading
        return {
            "file_id": file_id,
            "filename": file_path.name,
            "file_path": file_record.file_path,
            "size_bytes": file_size,
            "content": f"[File too large ({file_size} bytes). Use exec tool to read: cat or strings]",
            "is_binary": True,
        }

    # Try to read as text for small files
    try:
        content = file_path.read_text(encoding="utf-8")
        # Check if it looks like binary (contains null bytes)
        if "\x00" in content:
            return {
                "file_id": file_id,
                "filename": file_path.name,
                "file_path": file_record.file_path,
                "content": "[Binary file — content cannot be displayed as text]",
                "is_binary": True,
            }
        # Truncate for safety
        truncated = len(content) > 8000
        if truncated:
            content = content[:8000] + "\n...[truncated]"
        return {
            "file_id": file_id,
            "filename": file_path.name,
            "file_path": file_record.file_path,
            "content": content,
            "is_binary": False,
            "truncated": truncated,
        }
    except UnicodeDecodeError:
        return {
            "file_id": file_id,
            "filename": file_path.name,
            "file_path": file_record.file_path,
            "content": "[Binary file — content cannot be displayed as text]",
            "is_binary": True,
        }


@router.get("/user/{user_id}/tags", response_model=list[str])
async def get_user_tags(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """List all unique tags used by a user across their files."""
    return await get_all_user_tags(session, user_id)


@router.get("/user/{user_id}/search")
async def search_files_by_tag(
    user_id: int,
    tag: str,
    session: AsyncSession = Depends(get_session),
):
    """Find all files for a user that have a specific tag. Returns file records with their tags."""
    files = await find_files_by_tag(session, user_id, tag)
    if not files:
        return {"files": [], "tag": tag, "message": f"No files found with tag '{tag}'"}

    # Build response with file info and tags
    result = []
    for f in files:
        tags = await get_file_tags(session, f.id)
        result.append({
            "id": f.id,
            "file_path": f.file_path,
            "filename": f.file_path.split("/")[-1],
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "tags": tags,
        })
    return {"files": result, "tag": tag}


@router.post("/{file_id}/tags", response_model=list[str])
async def post_tags(
    file_id: int,
    body: list[str],
    session: AsyncSession = Depends(get_session),
):
    """Add tags to an existing file. Tags are case-normalized to lowercase."""
    result = await add_tags(session, file_id, body)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    return result


@router.delete("/{file_id}/tags", response_model=list[str])
async def delete_tags(
    file_id: int,
    body: list[str],
    session: AsyncSession = Depends(get_session),
):
    """Remove tags from a file. No error if tag doesn't exist."""
    success = await remove_tags(session, file_id, body)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    # Return remaining tags
    return await get_file_tags(session, file_id)
