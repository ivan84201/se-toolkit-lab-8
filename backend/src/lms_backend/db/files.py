"""Database operations for files and tags — with filesystem storage."""

import logging

from sqlalchemy import delete, text
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.models.file import FileRecord
from lms_backend.models.file_tag import FileTagRecord
from lms_backend.models.tag import TagRecord
from lms_backend import storage

logger = logging.getLogger(__name__)


# ===
# File operations
# ===


async def add_file(
    session: AsyncSession,
    user_id: int,
    filename: str,
    content: bytes,
    tags: list[str] | None = None,
) -> FileRecord:
    """Store file on filesystem and insert DB record with optional tags.

    Steps:
    1. Save file to filesystem (files/<user_id>/<filename>)
       - Raises FileExistsError (409) if file already exists
    2. Insert file record into database
    3. If tags provided: insert each tag (ignore duplicates), link in file_tags

    Disk deletion is attempted BEFORE DB deletion on failure, so DB state
    is never left orphaned.
    """
    # Step 1: Save to filesystem (raises FileExistsError if duplicate)
    relative_path = storage.save_file(user_id, filename, content)

    try:
        # Step 2: Insert DB record
        file_record = FileRecord(user_id=user_id, file_path=relative_path)
        session.add(file_record)
        await session.flush()  # Get file.id without committing

        # Step 3: Link tags if provided
        if tags:
            await _link_tags_to_file(session, file_record.id, tags)

        await session.commit()
        await session.refresh(file_record)
        return file_record
    except Exception:
        # Rollback: delete the filesystem file since DB insert failed
        await session.rollback()
        try:
            storage.delete_file(relative_path)
        except OSError:
            logger.error(
                "cleanup_failed",
                extra={
                    "event": "cleanup_failed",
                    "path": relative_path,
                },
            )
        raise


async def remove_file(session: AsyncSession, file_id: int) -> bool:
    """Remove file from filesystem and database.

    Disk deletion happens BEFORE DB deletion. If disk deletion fails,
    an OSError is raised and the DB record is NOT deleted.
    """
    file_record = await session.get(FileRecord, file_id)
    if file_record is None:
        return False

    # Step 1: Delete from filesystem first
    storage.delete_file(file_record.file_path)

    # Step 2: Delete file_tag rows (no FK CASCADE on this table)
    await session.exec(
        delete(FileTagRecord).where(FileTagRecord.file_id == file_id)
    )

    # Step 3: Delete from database
    await session.delete(file_record)
    await session.commit()
    return True


async def get_user_files(session: AsyncSession, user_id: int) -> list[FileRecord]:
    """Get all files belonging to a user."""
    result = await session.exec(
        select(FileRecord).where(FileRecord.user_id == user_id)
    )
    return list(result.all())


async def find_id_by_name(
    session: AsyncSession, user_id: int, filename: str
) -> int | None:
    """Find a file ID by filename for a specific user.
    
    Returns the file ID if found, None otherwise.
    """
    # Extract just the filename from the path (e.g., '123/myfile.pdf' -> 'myfile.pdf')
    # The file_path is stored as relative path like '123/myfile.pdf'
    result = await session.exec(
        select(FileRecord).where(
            FileRecord.user_id == user_id
        )
    )
    files = list(result.all())
    
    # Match against the filename (last part of file_path)
    for file_record in files:
        stored_name = file_record.file_path.split("/")[-1]
        if stored_name == filename:
            return file_record.id
    
    return None


# ===
# Tag operations
# ===


async def add_tags(
    session: AsyncSession,
    file_id: int,
    tags: list[str],
) -> list[str]:
    """Add tags to an existing file. Inserts tags if they don't exist. Avoids duplicates."""
    # Check file exists
    file_record = await session.get(FileRecord, file_id)
    if file_record is None:
        return []

    await _link_tags_to_file(session, file_id, tags)
    await session.commit()

    # Return the tag names that were linked
    result = await session.exec(
        select(TagRecord.name)
        .join(FileTagRecord, FileTagRecord.tag_id == TagRecord.id)
        .where(FileTagRecord.file_id == file_id)
    )
    return list(result.all())


async def remove_tags(
    session: AsyncSession,
    file_id: int,
    tags: list[str],
) -> bool:
    """Remove tags from a file. No error if tag doesn't exist."""
    # Normalize to lowercase
    tag_names = [t.lower() for t in tags]

    # Find matching tag IDs
    result = await session.exec(
        select(TagRecord.id).where(col(TagRecord.name).in_(tag_names))
    )
    tag_ids = list(result.all())

    if not tag_ids:
        return True  # Nothing to remove, not an error

    # Delete from file_tags
    stmt = (
        select(FileTagRecord)
        .where(FileTagRecord.file_id == file_id)
        .where(col(FileTagRecord.tag_id).in_(tag_ids))
    )
    file_tags = await session.exec(stmt)
    for ft in file_tags.all():
        await session.delete(ft)

    await session.commit()
    return True


async def get_file_tags(session: AsyncSession, file_id: int) -> list[str]:
    """Get all tag names for a file."""
    result = await session.exec(
        select(TagRecord.name)
        .join(FileTagRecord, FileTagRecord.tag_id == TagRecord.id)
        .where(FileTagRecord.file_id == file_id)
    )
    return list(result.all())


async def find_files_by_tag(
    session: AsyncSession, user_id: int, tag: str
) -> list[FileRecord]:
    """Find all files for a user that have a specific tag."""
    result = await session.exec(
        select(FileRecord)
        .join(FileTagRecord, FileTagRecord.file_id == FileRecord.id)
        .join(TagRecord, TagRecord.id == FileTagRecord.tag_id)
        .where(FileRecord.user_id == user_id)
        .where(TagRecord.name == tag.lower())
    )
    return list(result.all())


async def get_all_user_tags(session: AsyncSession, user_id: int) -> list[str]:
    """Get all unique tags used by a user across their files."""
    result = await session.exec(
        select(TagRecord.name)
        .join(FileTagRecord, FileTagRecord.tag_id == TagRecord.id)
        .join(FileRecord, FileRecord.id == FileTagRecord.file_id)
        .where(FileRecord.user_id == user_id)
        .distinct()
    )
    return list(result.all())


# ===
# Internal helpers
# ===


async def _link_tags_to_file(
    session: AsyncSession,
    file_id: int,
    tags: list[str],
) -> None:
    """Insert tags into tags table (ignore duplicates) and link to file in file_tags."""
    for tag_name in tags:
        normalized = tag_name.lower()

        # Insert tag if not exists (PostgreSQL ON CONFLICT DO NOTHING)
        tag_stmt = text(
            "INSERT INTO tag (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"
        )
        await session.exec(tag_stmt, params={"name": normalized})

        # Get the tag id
        tag_result = await session.exec(
            select(TagRecord.id).where(TagRecord.name == normalized)
        )
        tag_row = tag_result.first()
        if tag_row is None:
            continue

        # Link in file_tags (ignore if already linked)
        link_stmt = text(
            "INSERT INTO file_tag (file_id, tag_id) VALUES (:file_id, :tag_id) "
            "ON CONFLICT (file_id, tag_id) DO NOTHING"
        )
        await session.exec(link_stmt, params={"file_id": file_id, "tag_id": tag_row})
