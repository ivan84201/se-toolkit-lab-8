"""HTTP client for the nanobot OpenAI-compatible API server."""

import asyncio
import httpx
import json
import re

import logging

logger = logging.getLogger(__name__)


class NanobotClient:
    """Calls nanobot via its OpenAI-compatible HTTP API (nanobot serve)."""

    def __init__(self, api_base_url: str, model: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=api_base_url.rstrip("/"),
            timeout=120.0,
        )
        self._model = model

    async def ask(self, message: str) -> str:
        """Send a message to nanobot and return the response.

        nanobot serve is a stateless endpoint — each request starts a fresh
        agent session, so we only send the current user message.
        """
        try:
            response = await self._client.post(
                "/v1/chat/completions",
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": message}],
                    "max_tokens": 2048,
                    "temperature": 0.1,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            logger.info(f"Nanobot response: {answer[:100]}...")
            return answer
        except Exception as exc:
            logger.error(f"Nanobot communication error: {exc}")
            raise

    async def aclose(self) -> None:
        await self._client.aclose()

    async def suggest_tags(self, file_name: str, file_content: bytes) -> list[str]:
        """Send a file to nanobot and get tag suggestions.

        Analyzes the first ~3000 tokens of the file content and returns
        a list of relevant tags.
        """
        # Try to decode file content as text; if it fails, treat as binary
        try:
            text_content = file_content.decode("utf-8", errors="replace")
            # Truncate to ~3000 tokens (~4 chars per token average)
            max_chars = 3000 * 4
            if len(text_content) > max_chars:
                text_content = text_content[:max_chars] + "...[truncated]"
        except Exception:
            text_content = f"[Binary file: {file_name}]"

        prompt = (
            f"Analyze this file and suggest relevant tags. "
            f"File name: {file_name}\n\n"
            f"Content preview:\n{text_content}\n\n"
            f"Return ONLY a comma-separated list of lowercase tags, nothing else. "
            f"Examples: python,web,tutorial,draft\n"
            f"Tags:"
        )

        try:
            response = await self._client.post(
                "/v1/chat/completions",
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 256,
                    "temperature": 0.1,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip()

            # Parse comma-separated tags
            tags = [tag.strip() for tag in answer.split(",") if tag.strip()]
            # Clean up tags - remove quotes, ensure lowercase
            tags = [tag.strip("\"'").lower() for tag in tags]

            logger.info(f"Tag suggestions for {file_name}: {tags}")
            return tags
        except Exception as exc:
            logger.error(f"Tag suggestion failed for {file_name}: {exc}")
            raise
