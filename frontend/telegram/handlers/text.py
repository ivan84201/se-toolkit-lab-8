"""Handler for plain text messages (questions about files)."""

import logging
import re

from aiogram import Bot, types

logger = logging.getLogger(__name__)


def _looks_like_file_reference(text: str) -> bool:
    """Check if user message references a specific file name or ID."""
    # Match patterns like "file 123", "file_id: 45", "report.pdf", "ID: 12"
    patterns = [
        r'\bfile\s+id\s*[:=]?\s*\d+\b',  # "file id 123", "file id: 45"
        r'\bfile_id\s*[:=]?\s*\d+\b',     # "file_id: 123"
        r'\bid\s*[:=]?\s*\d+\b',          # "id: 123"
        r'\b\w+\.(pdf|txt|md|py|js|json|csv|docx?|xlsx?)\b',  # "report.pdf"
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


async def handle_text(message: types.Message, bot: Bot) -> None:
    """Handle plain text messages — forward to nanobot with structured prompt."""
    import context

    text = message.text
    if not text or text.startswith("/"):
        return

    # Show typing indicator while processing
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        user_id = message.from_user.id

        # Build a structured prompt to guide nanobot behavior
        if _looks_like_file_reference(text):
            # User specified a file - read it and answer immediately
            prompt = (
                f"The user is asking about a specific file. "
                f"User ID: {user_id}\n"
                f"User question: {text}\n\n"
                f"Instructions:\n"
                f"1. Use MCP tools to find the file path for user_id={user_id}\n"
                f"2. Call read_file_content to get the full filesystem path\n"
                f"3. Use the exec tool to read the file: `cat <path>` for text, `strings <path>` for PDFs\n"
                f"4. Answer the user's question based on the file content\n"
                f"5. Mention the source file name/ID in your answer"
            )
        else:
            # General question - use MCP tools to find relevant files
            prompt = (
                f"User ID: {user_id}\n"
                f"User question: {text}\n\n"
                f"You are an AI assistant with access to a file management system via MCP tools. "
                f"Always use user_id={user_id} when calling MCP tools.\n\n"
                f"Follow this workflow:\n\n"
                f"1. CHECK CLARITY: If the question is vague or ambiguous, respond with:\n"
                f"   \"I'm not sure what you're asking. Try using /help to see available commands.\n"
                f"   I can help you with: managing files (upload, view, tag), answering questions about your files, "
                f"and finding relevant documents.\"\n"
                f"   Then STOP.\n\n"
                f"2. DISCOVER TAGS: Call get_user_tags with user_id={user_id} to see what tags exist.\n"
                f"   Briefly mention available tags to the user.\n\n"
                f"3. FIND RELEVANT FILES: Use search_files_by_tag with tags that match the user's question. "
                f"If no relevant tags exist, call get_user_files to see all files.\n\n"
                f"4. GET FILE PATHS: Call read_file_content for each relevant file ID. This returns the full filesystem path.\n\n"
                f"5. READ FILES VIA EXEC: Use the exec tool to read each file:\n"
                f"   - For text files: `cat <path>` or `head -n 100 <path>`\n"
                f"   - For PDFs/binary: `strings <path>` (extracts readable text)\n\n"
                f"6. ANSWER WITH SOURCES: Answer the user's question using information from the file content. "
                f"Always mention which file(s) (filename or ID) you found the information in.\n\n"
                f"7. INSUFFICIENT DATA: If you could not find enough information, say:\n"
                f"   \"I could not find enough information in your files to answer this question. "
                f"Try uploading relevant files or asking a more specific question.\""
            )

        answer = await context.nanobot_client.ask(prompt)
        await message.answer(answer)
    except Exception as exc:
        logger.error(f"Failed to get response from nanobot: {exc}")
        await message.answer(
            "⚠️ I couldn't reach the AI assistant. Please try again later."
        )
