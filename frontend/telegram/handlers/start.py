"""Handler for /start command."""

from aiogram import types


async def handle_start(message: types.Message) -> None:
    """Respond to /start with a brief welcome and point to /help."""
    text = (
        "👋 Welcome! I'm your file assistant.\n\n"
        "I can store your files, suggest tags, and answer questions about them.\n"
        "Send /help to see everything I can do."
    )
    await message.answer(text)
