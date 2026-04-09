# Telegram Frontend for File Tagging & Retrieval System

## 🎯 Goal

Enable users to interact with the file tagging system via Telegram: upload files, manage tags, browse files, and ask questions.

## 🏗️ Architecture

```
Telegram User
    ↓
aiogram Bot (frontend/telegram/)
    ↓ HTTP (Bearer auth)
Backend API (backend/src/lms_backend/)
    ↓
PostgreSQL + files/ directory
```

The bot calls the backend API directly (not through MCP). MCP is reserved for the LLM (nanobot) layer.

## 🛠️ Features & Commands

### 1. File Upload (Send Document)
- **Trigger**: Send a document to the bot
- **Flow**: Download from Telegram → temp directory → `POST /files/` → cleanup temp file
- **Response**: Confirmation with file ID and path

### 2. `/myfiles`
- Lists all files for the user with ID, name, and upload date

### 3. `/tags <file_id>`
- Shows all tags attached to a file

### 4. `/addtags <file_id> tag1, tag2`
- Adds tags to a file (comma-separated)

### 5. `/removetags <file_id> tag1, tag2`
- Removes specified tags from a file

### 6. `/delete <file_id>`
- Deletes a file (both disk and database)

### 7. Plain text messages
- User types a question about their files
- Placeholder: acknowledges the question (LLM integration TODO)
- When connected: forwards to LLM via MCP, which uses file tagging tools to answer

## 📁 Project Structure

```
frontend/telegram/
├── bot.py                    # Entry point, --test mode, dispatcher setup
├── config.py                 # Settings from env vars (BOT_TOKEN, BACKEND_URL, BACKEND_API_KEY)
├── pyproject.toml            # Dependencies: aiogram, httpx
├── handlers/
│   ├── __init__.py
│   ├── start.py              # /start handler
│   ├── commands.py           # /myfiles, /tags, /addtags, /removetags, /delete
│   └── document.py           # File upload handler (document messages)
└── services/
    ├── __init__.py
    └── api_client.py         # HTTP client for backend API
```

## 🔑 Key Patterns

### Separation of Concerns
- **Handlers** are plain async functions that take a `Message` and call `message.answer()`.
- **Services** (`api_client.py`) handle HTTP communication with the backend.
- **Config** loads settings from environment variables.
- The same handler logic works from `--test` mode, unit tests, or live Telegram.

### Test Mode
```bash
BOT_TOKEN=xxx BACKEND_URL=http://localhost:8000 BACKEND_API_KEY=xxx uv run bot.py --test "/start"
```
Creates a fake `Message` object, routes to the handler, captures `message.answer()` output.

### File Upload Flow
1. User sends document → `handle_document` triggered
2. Download via Telegram Bot API to `tmp/<user_id>/<filename>`
3. Upload to backend via `POST /files/` (multipart form)
4. Cleanup temp file
5. Handle duplicates (409), errors gracefully

### Temp Files
- Root: `tmp/` created via `tempfile.mkdtemp(prefix="tg-bot-")`
- Per-user subfolders: `tmp/<user_id>/`
- Always cleaned up after upload

## ⚙️ Configuration

| Env Var | Description |
|---------|-------------|
| `BOT_TOKEN` | Telegram bot token from @BotFather |
| `BACKEND_URL` | Backend API base URL (e.g., `http://localhost:8002`) |
| `BACKEND_API_KEY` | Bearer token for backend authentication |

## 🚀 Running

```bash
# Sync dependencies
cd frontend/telegram && uv sync

# Test mode
BOT_TOKEN=xxx BACKEND_URL=http://localhost:8002 BACKEND_API_KEY=xxx uv run bot.py --test "/start"

# Live mode (polling)
BOT_TOKEN=<real-token> BACKEND_URL=http://localhost:8002 BACKEND_API_KEY=xxx uv run bot.py
```
