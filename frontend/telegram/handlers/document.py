"""Handler for document messages (file uploads)."""

import logging
import uuid

from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.api_client import APIError, FileNotFoundError_, DuplicateFileError, ServerError, ClientError

logger = logging.getLogger(__name__)

# In-memory store for pending tag suggestions.
# Key: short uuid (used in callback_data), Value: {"file_id": int, "tags": list[str]}
# Entries are cleaned up after user approves/rejects.
_pending_tag_suggestions: dict[str, dict] = {}


def _store_tag_suggestions(file_id: int, tags: list[str]) -> str:
    """Store tag suggestions in memory and return a short lookup key."""
    key = uuid.uuid4().hex[:8]
    _pending_tag_suggestions[key] = {"file_id": file_id, "tags": tags}
    return key


def _get_tag_suggestions(key: str) -> dict | None:
    """Retrieve and remove tag suggestions by key."""
    return _pending_tag_suggestions.pop(key, None)


async def handle_document(message: types.Message) -> None:
    """Handle a document (file) sent by the user.

    Downloads the file to a temp directory, uploads it to the backend,
    then asks nanobot to suggest tags. Presents user with option to add them.
    """
    import json
    import context

    api_client = context.api_client
    tmp_dir = context.tmp_dir

    doc = message.document
    if doc is None:
        return

    file_name = doc.file_name or "unnamed_file"
    user_id = message.from_user.id

    await message.answer(f"⏳ Downloading {file_name}...")

    # Download file from Telegram
    file_obj = await message.bot.get_file(doc.file_id)
    dest = tmp_dir / str(user_id) / file_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    await message.bot.download_file(file_obj.file_path, dest)

    # Upload to backend
    try:
        result = await api_client.upload_file(user_id, str(dest))
    except DuplicateFileError:
        await message.answer(
            f"⚠️ Error 409: a file named {file_name} already exists for you. "
            "Delete the old one first with /delete or rename this file."
        )
        return
    except ServerError as exc:
        logger.exception("upload_failed")
        await message.answer(f"⚠️ Error {exc.status_code}: server error during upload. Try again later.")
        return
    except APIError as exc:
        logger.exception("upload_failed")
        await message.answer(f"⚠️ Error {exc.status_code}: upload failed. {exc.message}")
        return

    await message.answer(
        f"✅ File uploaded!\n"
        f"📄 {file_name}\n"
        f"🆔 ID: {result.id}\n"
    )

    # Read file content before cleanup for nanobot tag suggestions
    try:
        file_content = dest.read_bytes()
    except Exception:
        logger.warning("Failed to read file for tag suggestions")
        file_content = b""

    # Clean up temp file
    if dest.exists():
        dest.unlink()

    # Ask nanobot to suggest tags
    if file_content:
        await message.answer(f"🤖 Analyzing {file_name} for tag suggestions...")
        try:
            suggested_tags = await context.nanobot_client.suggest_tags(
                file_name=file_name,
                file_content=file_content,
            )

            if not suggested_tags:
                await message.answer("📭 Could not generate tag suggestions for this file.")
                return

            # Store suggestions in memory and get a short key for the callback
            callback_key = _store_tag_suggestions(result.id, suggested_tags)

            # Show suggested tags with approve/reject buttons
            tags_str = ", ".join(suggested_tags)
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Add tags",
                            callback_data=f"tag:a:{callback_key}",
                        ),
                        InlineKeyboardButton(
                            text="❌ Skip",
                            callback_data=f"tag:r:{callback_key}",
                        ),
                    ]
                ]
            )
            await message.answer(
                f"🏷️ Suggested tags for {file_name}:\n{tags_str}\n\n"
                f"Would you like to add these tags?",
                reply_markup=keyboard,
            )
        except Exception as exc:
            logger.warning("tag_suggestion_failed", exc_info=exc)
            await message.answer("⚠️ Could not generate tag suggestions. You can add tags manually with /addtags.")
