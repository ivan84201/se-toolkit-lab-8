"""Handler for inline keyboard callbacks (e.g., approve/reject suggested tags)."""

import logging

from aiogram import types

from handlers.document import _get_tag_suggestions
from services.api_client import APIError, FileNotFoundError_, ServerError

logger = logging.getLogger(__name__)


async def handle_tag_action_callback(callback_query: types.CallbackQuery) -> None:
    """Handle approve/reject callbacks for suggested tags.

    Callback data format: tag:{a|r}:{callback_key}
    where 'a' = approve, 'r' = reject, and callback_key is a short uuid
    that maps to in-memory stored suggestions.
    """
    import context

    data = callback_query.data
    parts = data.split(":", 2)
    if len(parts) != 3 or parts[0] != "tag":
        await callback_query.answer("⚠️ Invalid callback data")
        return

    action = parts[1]  # "a" or "r"
    callback_key = parts[2]

    suggestion = _get_tag_suggestions(callback_key)
    if suggestion is None:
        await callback_query.answer("⚠️ Tag suggestions expired. Use /addtags to add tags manually.")
        return

    file_id = suggestion["file_id"]
    tags = suggestion["tags"]

    if action == "a":
        try:
            result_tags = await context.api_client.add_tags(file_id, tags)
            tags_str = ", ".join(result_tags)
            await callback_query.message.edit_text(
                f"✅ Tags added!\n{tags_str}",
            )
        except FileNotFoundError_:
            await callback_query.message.edit_text(f"⚠️ Error 404: file {file_id} not found.")
        except ServerError as exc:
            logger.exception("tag_add_failed")
            await callback_query.message.edit_text(
                f"⚠️ Error {exc.status_code}: server error while adding tags. Try again later with /addtags."
            )
        except APIError as exc:
            logger.exception("tag_add_failed")
            await callback_query.message.edit_text(
                f"⚠️ Error {exc.status_code}: {exc.message}"
            )
    elif action == "r":
        await callback_query.message.edit_text(
            "👍 Tags skipped. You can always add them later with /addtags.",
        )

    # Acknowledge the callback to remove the loading indicator
    await callback_query.answer()
