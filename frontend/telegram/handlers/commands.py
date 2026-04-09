"""Handlers for /myfiles, /tags, /addtags, /removetags, /delete commands."""

import logging
from aiogram import types
from aiogram.types import BufferedInputFile

from services.api_client import APIError, FileNotFoundError_, DuplicateFileError, ServerError, ClientError

logger = logging.getLogger(__name__)


def _parse_file_identifier(text: str) -> str | None:
    """Extract file ID or filename from command text like '/tags 12' or '/tags report.pdf'."""
    parts = text.split()
    if len(parts) < 2:
        return None
    return parts[1]


async def _resolve_file_id(api_client, user_id: int, identifier: str) -> int | None:
    """Resolve a file identifier - if it's a number, use it directly; otherwise look up by name."""
    # Try parsing as integer ID first
    try:
        return int(identifier)
    except ValueError:
        pass

    # Otherwise, look up by filename
    try:
        return await api_client.get_file_by_name(user_id, identifier)
    except APIError:
        return None


def _parse_tags(text: str) -> list[str] | None:
    """Extract space-separated tags from text after file_id."""
    parts = text.split()
    if len(parts) < 3:
        return None
    return [t.strip() for t in parts[2:] if t.strip()]


async def handle_myfiles(message: types.Message) -> None:
    """/myfiles [tag1 tag2 ...] — list all files for the user, optionally filtered by tags."""
    import context

    user_id = message.from_user.id
    api_client = context.api_client

    # Parse tags: space-separated words after /myfiles
    parts = message.text.split()
    requested_tags = [t.lower() for t in parts[1:] if t.strip()] if len(parts) > 1 else []

    try:
        files = await api_client.get_user_files(user_id)
    except FileNotFoundError_:
        await message.answer("📭 You have no uploaded files yet.")
        return
    except ClientError as exc:
        await message.answer(f"⚠️ Error {exc.status_code}: could not fetch files. {exc.message}")
        return
    except ServerError as exc:
        await message.answer(f"⚠️ Error {exc.status_code}: server error while fetching files. Try again later.")
        return
    except APIError as exc:
        await message.answer(f"⚠️ Error {exc.status_code}: {exc.message}")
        return

    if not files:
        await message.answer("📭 You have no uploaded files yet.")
        return

    # Filter by tags if provided
    if requested_tags:
        filtered_files = []
        for f in files:
            try:
                file_tags = await api_client.get_file_tags(f.id)
                file_tags_lower = {t.lower() for t in file_tags}
                # Check if file has ALL requested tags
                if all(tag in file_tags_lower for tag in requested_tags):
                    filtered_files.append(f)
            except Exception:
                logger.warning("Failed to fetch tags for file %s", f.id)
                continue
        files = filtered_files

        if not files:
            tags_str = " ".join(requested_tags)
            await message.answer(f"📭 No files found with tags: {tags_str}")
            return

    for f in files:
        name = f.file_path.split("/")[-1]
        try:
            file_bytes = await api_client.download_file(f.id)
            await message.answer_document(
                document=BufferedInputFile(file_bytes, filename=name),
                caption=f"📄 {name} (ID: {f.id}) — {f.created_at[:10]}",
            )
        except FileNotFoundError_ as exc:
            logger.error("download_failed", exc_info=exc)
            await message.answer(f"⚠️ Error 404: file {name} (ID: {f.id}) not found.")
        except ServerError as exc:
            logger.error("download_failed", exc_info=exc)
            await message.answer(f"⚠️ Error {exc.status_code}: server error loading {name} (ID: {f.id}). Try again later.")
        except APIError as exc:
            logger.error("download_failed", exc_info=exc)
            await message.answer(f"⚠️ Error {exc.status_code}: failed to load {name} (ID: {f.id}). {exc.message}")


async def handle_tags(message: types.Message) -> None:
    """/tags <file_id_or_name> — show tags for a file."""
    import context

    api_client = context.api_client
    user_id = message.from_user.id

    identifier = _parse_file_identifier(message.text)
    if identifier is None:
        await message.answer("⚠️ Usage: /tags <file_id_or_name>")
        return

    file_id = await _resolve_file_id(api_client, user_id, identifier)
    if file_id is None:
        await message.answer(f"⚠️ File '{identifier}' not found.")
        return

    try:
        tags = await api_client.get_file_tags(file_id)
    except FileNotFoundError_:
        await message.answer(f"⚠️ Error 404: file {file_id} not found.")
        return
    except ServerError as exc:
        await message.answer(f"⚠️ Error {exc.status_code}: server error while fetching tags. Try again later.")
        return
    except APIError as exc:
        await message.answer(f"⚠️ Error {exc.status_code}: {exc.message}")
        return

    if not tags:
        await message.answer(f"📄 File {file_id} has no tags.")
    else:
        tag_list = "\n".join(f"🏷️ {t}" for t in tags)
        await message.answer(f"🏷️ Tags for file {file_id}:\n{tag_list}")


async def handle_addtags(message: types.Message) -> None:
    """/addtags <file_id_or_name> tag1 tag2 — add tags to a file."""
    import context

    api_client = context.api_client
    user_id = message.from_user.id

    identifier = _parse_file_identifier(message.text)
    tags = _parse_tags(message.text)

    if identifier is None or not tags:
        await message.answer("⚠️ Usage: /addtags <file_id_or_name> <tag1> <tag2>")
        return

    file_id = await _resolve_file_id(api_client, user_id, identifier)
    if file_id is None:
        await message.answer(f"⚠️ File '{identifier}' not found.")
        return

    try:
        result = await api_client.add_tags(file_id, tags)
    except FileNotFoundError_:
        await message.answer(f"⚠️ Error 404: file {file_id} not found.")
        return
    except ServerError as exc:
        await message.answer(f"⚠️ Error {exc.status_code}: server error while adding tags. Try again later.")
        return
    except APIError as exc:
        await message.answer(f"⚠️ Error {exc.status_code}: {exc.message}")
        return

    await message.answer(f"✅ Tags added. File now has: {', '.join(result)}")


async def handle_removetags(message: types.Message) -> None:
    """/removetags <file_id_or_name> tag1 tag2 — remove tags from a file."""
    import context

    api_client = context.api_client
    user_id = message.from_user.id

    identifier = _parse_file_identifier(message.text)
    tags = _parse_tags(message.text)

    if identifier is None or not tags:
        await message.answer("⚠️ Usage: /removetags <file_id_or_name> <tag1> <tag2> ...")
        return

    file_id = await _resolve_file_id(api_client, user_id, identifier)
    if file_id is None:
        await message.answer(f"⚠️ File '{identifier}' not found.")
        return

    try:
        result = await api_client.remove_tags(file_id, tags)
    except FileNotFoundError_:
        await message.answer(f"⚠️ Error 404: file {file_id} not found.")
        return
    except ServerError as exc:
        await message.answer(f"⚠️ Error {exc.status_code}: server error while removing tags. Try again later.")
        return
    except APIError as exc:
        await message.answer(f"⚠️ Error {exc.status_code}: {exc.message}")
        return

    if result:
        await message.answer(f"✅ Tags removed. Remaining: {', '.join(result)}")
    else:
        await message.answer("✅ All specified tags removed. No tags remaining.")


async def handle_delete(message: types.Message) -> None:
    """/delete <file_id_or_name> — delete a file and its tags."""
    import context

    api_client = context.api_client
    user_id = message.from_user.id

    identifier = _parse_file_identifier(message.text)
    if identifier is None:
        await message.answer("⚠️ Usage: /delete <file_id_or_name>")
        return

    file_id = await _resolve_file_id(api_client, user_id, identifier)
    if file_id is None:
        await message.answer(f"⚠️ File '{identifier}' not found.")
        return

    try:
        await api_client.delete_file(file_id, user_id)
    except FileNotFoundError_:
        await message.answer(f"⚠️ Error 404: file {file_id} not found.")
        return
    except ServerError as exc:
        await message.answer(f"⚠️ Error {exc.status_code}: server error while deleting file. Try again later.")
        return
    except APIError as exc:
        await message.answer(f"⚠️ Error {exc.status_code}: {exc.message}")
        return

    await message.answer(f"🗑️ File {file_id} deleted.")


async def handle_help(message: types.Message) -> None:
    """/help — show detailed command descriptions."""
    text = (
        "📋 Available commands:\n\n"
        "📁 /myfiles (optional) <tag1> <tag2> ...\n"
        "    List all your uploaded files.\n"
        "    Optionally show files only with included tags.\n"
        "    Each file is sent back as a downloadable attachment.\n\n"
        "🏷️ /tags <file_id_or_name>\n"
        "    Show all tags assigned to a file.\n"
        "    Use the numeric ID or the filename.\n\n"
        "➕ /addtags <file_id_or_name> <tag1> <tag2> ...\n"
        "    Add one or more tags to a file.\n\n"
        "➖ /removetags <file_id_or_name> <tag1> <tag2> ...\n"
        "    Remove tags from a file.\n\n"
        "🗑️ /delete <file_id_or_name>\n"
        "    Permanently delete a file.\n\n"
        "💬 Plain text messages\n"
        "    Ask questions about your files — I will answer.\n\n"
        "📎 Send a file\n"
        "    I'll store it, analyze it, and suggest tags."
    )
    await message.answer(text)
