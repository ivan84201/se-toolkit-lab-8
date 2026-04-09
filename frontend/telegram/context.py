"""Shared application context — holds globals that handlers need.

This module exists so that bot.py (run as __main__) and the handlers
(import bot / from handlers.xxx) share the SAME variables.  Without
this, `python bot.py` puts globals in __main__ while `import bot`
creates a separate copy that stays None.
"""

from pathlib import Path
import tempfile

# Shared API client — set during bot startup
api_client = None  # type: ignore[assignment]

# Shared nanobot client — set during bot startup
nanobot_client = None  # type: ignore[assignment]

# Temporary directory for downloaded Telegram files
tmp_dir = Path(tempfile.mkdtemp(prefix="tg-bot-"))
