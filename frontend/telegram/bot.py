"""Telegram bot entry point with --test mode."""

import argparse
import asyncio
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from config import load_settings
from handlers.commands import (
    handle_addtags,
    handle_delete,
    handle_help,
    handle_myfiles,
    handle_removetags,
    handle_tags,
)
from handlers.callbacks import handle_tag_action_callback
from handlers.document import handle_document
from handlers.start import handle_start
from handlers.text import handle_text

logger = logging.getLogger(__name__)


def create_dispatcher() -> Dispatcher:
    """Create and configure the dispatcher with all handlers."""
    dp = Dispatcher()

    # Commands
    dp.message.register(handle_start, Command("start"))
    dp.message.register(handle_help, Command("help"))
    dp.message.register(handle_myfiles, Command("myfiles"))
    dp.message.register(handle_tags, Command("tags"))
    dp.message.register(handle_addtags, Command("addtags"))
    dp.message.register(handle_removetags, Command("removetags"))
    dp.message.register(handle_delete, Command("delete"))

    # Document uploads
    dp.message.register(handle_document, lambda m: m.document is not None)

    # Inline keyboard callbacks
    dp.callback_query.register(handle_tag_action_callback)

    # Plain text messages (non-command) — for LLM questions
    dp.message.register(
        handle_text, lambda m: m.text and not m.text.startswith("/")
    )

    return dp


async def run_bot(token: str, backend_url: str, api_key: str, nanobot_api_url: str, llm_model: str) -> None:
    """Run the bot in polling mode."""
    import context
    from services.api_client import APIClient
    from services.nanobot_client import NanobotClient

    context.api_client = APIClient(base_url=backend_url, api_key=api_key)
    context.nanobot_client = NanobotClient(
        api_base_url=nanobot_api_url, model=llm_model
    )

    bot = Bot(token=token)
    dp = create_dispatcher()
    try:
        logger.info("bot_started")
        await dp.start_polling(bot)
    finally:
        await context.api_client.aclose()


def _make_test_message(text: str, user_id: int = 1) -> types.Message:
    """Build a fake Message for test mode."""
    return types.Message(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="Tester"),
        text=text,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram bot for file tagging")
    parser.add_argument("--test", type=str, help="Test a command, e.g. '/start'")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    if args.test:
        settings = load_settings()

        async def run_test() -> None:
            responses: list[str] = []

            async def capture(*a: object, **kw: object) -> None:
                for arg in a:
                    if isinstance(arg, str):
                        responses.append(arg)
                        return
                if "text" in kw:
                    responses.append(str(kw["text"]))

            import context
            from services.api_client import APIClient
            from services.nanobot_client import NanobotClient

            context.api_client = APIClient(
                base_url=settings.BACKEND_URL, api_key=settings.BACKEND_API_KEY
            )
            context.nanobot_client = NanobotClient(
                api_base_url=settings.NANOBOT_API_URL,
                model=settings.LLM_API_MODEL,
            )

            cmd = args.test.lstrip("/")

            # Route document messages
            is_doc = cmd.startswith("doc:")
            if is_doc:
                file_path = cmd[4:]
                msg = _make_test_message("", 123)
                msg.document = types.Document(
                    file_id="test", file_name=Path(file_path).name
                )

                with patch.object(types.Message, "answer", new=capture):
                    await handle_document(msg)
            else:
                cmd_name = cmd.split()[0]  # "tags 1" -> "tags"
                handler_map = {
                    "start": handle_start,
                    "help": handle_help,
                    "myfiles": handle_myfiles,
                    "tags": handle_tags,
                    "addtags": handle_addtags,
                    "removetags": handle_removetags,
                    "delete": handle_delete,
                }
                handler = handler_map.get(cmd_name)

                msg = _make_test_message(f"/{cmd}", 123)
                if handler is None:
                    print(f"[test] No handler for /{cmd}")
                    return

                with patch.object(types.Message, "answer", new=capture):
                    await handler(msg)

            print(f"[test] Command: {args.test}")
            if responses:
                print(f"[test] Response:\n{responses[0]}")
            else:
                print("[test] No response captured")

        asyncio.run(run_test())
    else:
        settings = load_settings()
        asyncio.run(
            run_bot(
                settings.BOT_TOKEN,
                settings.BACKEND_URL,
                settings.BACKEND_API_KEY,
                settings.NANOBOT_API_URL,
                settings.LLM_API_MODEL,
            )
        )


if __name__ == "__main__":
    main()
