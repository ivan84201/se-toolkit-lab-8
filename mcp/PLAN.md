# MCP Server for File Tagging & Retrieval System

## 🎯 Objective

Build an MCP (Model Context Protocol) server that allows an LLM (nanobot) to:

- Store files and metadata in PostgreSQL
- Generate and attach tags to files
- Retrieve files by user or tags
- Serve as the bridge between Telegram bot (frontend), PostgreSQL database, and LLM (Nanobot/Qwen)

## 🧠 Responsibilities of MCP

The MCP server is the LLM's tool interface. It exposes structured tools that the LLM can call.

MCP must:
- Translate LLM tool calls → database operations via the backend API
- Return structured JSON responses
- Enforce validation and normalization (tags → lowercase)
- Handle errors safely

## 🛠️ Available Tools

### `add_file`
Add a new file record with optional tags.
- **Parameters**: `user_id` (int), `file_path` (str), `tags` (list[str], optional)
- **API**: `POST /files/`

### `delete_file`
Delete a file record and all its attached tags (CASCADE).
- **Parameters**: `file_id` (int)
- **API**: `DELETE /files/{file_id}`

### `get_user_files`
List all files uploaded by a specific user.
- **Parameters**: `user_id` (int)
- **API**: `GET /files/user/{user_id}`

### `get_file_tags`
Get all tags attached to a specific file.
- **Parameters**: `file_id` (int)
- **API**: `GET /files/{file_id}/tags`

### `add_tags`
Attach tags to an existing file. Tags are normalized to lowercase and deduplicated.
- **Parameters**: `file_id` (int), `tags` (list[str])
- **API**: `POST /files/{file_id}/tags`

### `remove_tags`
Remove specific tags from a file. No error if tags don't exist.
- **Parameters**: `file_id` (int), `tags` (list[str])
- **API**: `DELETE /files/{file_id}/tags`

## 📁 Project Structure

```
mcp/mcp-lms/
├── src/mcp_lms/
│   ├── __init__.py       # Public API exports
│   ├── __main__.py       # python -m mcp_lms entry point
│   ├── client.py         # Async HTTP client for backend API
│   ├── models.py         # Pydantic response models (FileRecord, TagRecord, FileWithTag)
│   ├── server.py         # MCP stdio server with tool registry
│   ├── settings.py       # Settings (base_url, api_key from env vars)
│   └── tools.py          # Tool specs, schemas, handlers, registry
└── pyproject.toml
```

## 🔧 Architecture

```
LLM (Nanobot)
    ↓ tool call
MCP Server (stdio)
    ↓ HTTP (Bearer auth)
Backend API (FastAPI)
    ↓ async SQLAlchemy
PostgreSQL (file, tag, file_tag, user tables)
```

## ⚙️ Settings

- `NANOBOT_LMS_BACKEND_URL` or `NANOBOT_LMS_BACKEND_URL` env var — backend base URL
- `NANOBOT_LMS_API_KEY` or `LMS_API_KEY` env var — Bearer token for API auth

## 🧪 Edge Cases

- Tags are case-normalized to lowercase
- Duplicate tags are ignored (no error)
- Removing non-existent tags → no error
- File not found → 404 returned as error text
