---
name: lms
description: Use LMS MCP tools for file tagging and retrieval
always: true
---

# LMS Skill

You have access to the LMS (Learning Management System) MCP server tools for managing files and tags in PostgreSQL. Use these tools to upload files, attach tags, search files by tags, read file content, and retrieve files by user or tag.

## Available LMS Tools

### `get_user_files`
List all files uploaded by a specific user.
- **Parameters**:
  - `user_id` (required): Telegram user identifier
- **Returns**: Array of file records (id, user_id, file_path, created_at)
- **Use when**: You need to see what files a user has, or find a file ID by name/date

### `get_user_tags`
List all unique tags used by a specific user across all their files.
- **Parameters**:
  - `user_id` (required): Telegram user identifier
- **Returns**: Flat list of tag name strings (e.g. ["python", "tutorial", "draft"])
- **Use when**: You need to discover what topics/tags exist for a user. **Call this FIRST** before searching by tag.

### `search_files_by_tag`
Find all files for a user that have a specific tag.
- **Parameters**:
  - `user_id` (required): Telegram user identifier
  - `tag` (required): Tag name to search for (case-insensitive)
- **Returns**: Object with `files` (array of file records with their tags), `tag`, and `message`
- **Use when**: You need to find files relevant to a topic. Use `get_user_tags` first to discover available tags.

### `read_file_content`
Get the filesystem path of a file so you can read its content via the exec tool.
- **Parameters**:
  - `file_id` (required): ID of the file to read
- **Returns**: Object with `file_id`, `filename`, `file_path` (full path inside container), `is_binary`, and a `message` with exec commands to use
- **Use when**: You need to actually read what's inside a file. Use this AFTER finding relevant files via `get_user_files` or `search_files_by_tag`.
- **How to read the file**: After calling this tool, use the **exec tool** with one of these commands:
  - `cat <file_path>` — for text files (.py, .md, .txt, .json, etc.)
  - `head -n 50 <file_path>` — for preview (first 50 lines)
  - `strings <file_path>` — for binary/PDF files to extract readable text strings
  - `wc -l <file_path>` — to check how many lines a file has
- **Note**: This works for ALL file types including PDFs, because the exec tool runs shell commands that can handle binary.

### `get_file_tags`
Get all tags attached to a specific file.
- **Parameters**:
  - `file_id` (required): ID of the file
- **Returns**: Array of tag names (strings)
- **Use when**: User asks what tags a file has, or you need to check existing tags

### `add_file`
Upload a file from the local filesystem to the user's storage.
- **Parameters**:
  - `user_id` (required): Telegram user identifier
  - `file_path` (required): **Local filesystem path** on the MCP server, e.g. `/tmp/report.pdf`
  - `tags` (optional): List of tag strings
- **Returns**: File record with id, user_id, file_path, created_at
- **Note**: Returns 409 if file with same name already exists for that user.

### `add_tags`
Attach tags to an existing file. Tags normalized to lowercase and deduplicated.
- **Parameters**:
  - `file_id` (required): ID of the file
  - `tags` (required): List of tag strings
- **Returns**: Array of all tag names now attached to the file

### `remove_tags`
Remove specific tags from a file. No error if tags don't exist.
- **Parameters**:
  - `file_id` (required): ID of the file
  - `tags` (required): List of tag strings to remove
- **Returns**: Array of remaining tag names

### `delete_file`
Delete a file record and all its attached tags.
- **Parameters**:
  - `file_id` (required): ID of the file to delete

## Strategy Rules — How to Navigate the Database

**Follow this workflow when answering questions about files:**

1. **Discover available tags** → Call `get_user_tags` with the user's `user_id` to see what topics exist.

2. **Find relevant files** → Use `search_files_by_tag` with tags that match the user's question. Or use `get_user_files` if they asked about all their files.

3. **Get file paths** → Call `read_file_content` for each relevant file ID. This returns the full filesystem path.

4. **Read file content via exec** → Use the **exec tool** to read the file:
   - For text files: `cat <path>` or `head -n 100 <path>`
   - For PDFs/binary: `strings <path>` (extracts readable text from any binary file)
   - Check file size first: `wc -c <path>` if the file might be large

5. **Answer with sources** → Use the information from the file content to answer. Always mention which file(s) you found the info in (filename or ID).

6. **Handle insufficient data** → If no relevant tags exist or files don't contain enough info, say: "I could not find enough information in your files to answer this question. Try uploading relevant files or asking a more specific question."

**Tag normalization**: Tags are lowercase. "Python" == "python".

**File identification**: When user refers to a file by description, use `get_user_files` first to find matching file, then use its ID.

**Batch operations**: Call `add_tags` once with all tags, not multiple calls.

**Context awareness**: Always use the correct `user_id` from context.

## Example Interactions

**User**: "What files do I have?"
→ Call `get_user_files` with user_id. Show the list.

**User**: "What tags do I have?"
→ Call `get_user_tags` with user_id. Show the list.

**User**: "Tell me about Python"
→ Step 1: Call `get_user_tags` to see available tags.
→ Step 2: If "python" exists, call `search_files_by_tag` with tag="python".
→ Step 3: Call `read_file_content` for each relevant file to get the path.
→ Step 4: Use exec: `strings <path>` to read the file content.
→ Step 5: Answer based on content, mentioning source files.

**User**: "Find files tagged tutorial"
→ Call `search_files_by_tag` with user_id, tag="tutorial".

**User**: "What's in file 5?"
→ Call `read_file_content` with file_id=5 to get the path.
→ Use exec: `cat <path>` (or `strings <path>` if binary) to read it.
→ Show the content.

**User**: "Tag my last file with 'important' and 'review-needed'"
→ Call `get_user_files` to find most recent file, then `add_tags`.

**User**: "What's the difference between my two Python files?"
→ Call `search_files_by_tag` with tag="python", then `read_file_content` for each, then compare.
