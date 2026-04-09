"""Async HTTP client for the backend file tagging & retrieval API."""

from __future__ import annotations

from typing import Any, TypeVar

import httpx
from pydantic import BaseModel
from mcp_lms.models import FileRecord, TagRecord


ModelT = TypeVar("ModelT", bound=BaseModel)


class LMSClient:
    """Client for the backend file tagging & retrieval API."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._owns_client = http_client is None
        self._http_client = http_client or httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    async def __aenter__(self) -> LMSClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http_client.aclose()

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str | int] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        response = await self._http_client.request(method, path, params=params, json=json)
        response.raise_for_status()
        return response.json()

    async def _get_list(
        self,
        path: str,
        model: type[ModelT],
        *,
        params: dict[str, str | int] | None = None,
    ) -> list[ModelT]:
        payload = await self._request_json("GET", path, params=params)
        return [model.model_validate(item) for item in payload]

    async def _get_model(
        self,
        path: str,
        model: type[ModelT],
        *,
        params: dict[str, str | int] | None = None,
    ) -> ModelT:
        payload = await self._request_json("GET", path, params=params)
        return model.model_validate(payload)

    async def _delete(self, path: str) -> dict[str, Any]:
        response = await self._http_client.delete(path)
        response.raise_for_status()
        return {}

    # === File operations ===

    async def add_file(
        self, user_id: int, file_path: str, tags: list[str] | None = None
    ) -> FileRecord:
        """Add a file by path. The server reads the file content and stores it.

        `file_path` here is a local filesystem path the MCP server can read.
        The upload uses multipart form data: the server stores it as
        files/<user_id>/<filename>.
        """
        from pathlib import Path

        local_path = Path(file_path)
        if not local_path.is_file():
            raise FileNotFoundError(f"Local file not found: {file_path}")

        content = local_path.read_bytes()
        tag_str = ",".join(tags) if tags else None

        response = await self._http_client.post(
            "/files/",
            data={"user_id": user_id, "tags": tag_str},
            files={"file": (local_path.name, content, "application/octet-stream")},
        )
        response.raise_for_status()
        return FileRecord.model_validate(response.json())

    async def delete_file(self, file_id: int) -> dict[str, Any]:
        return await self._delete(f"/files/{file_id}")

    async def get_user_files(self, user_id: int) -> list[FileRecord]:
        return await self._get_list(f"/files/user/{user_id}", FileRecord)

    # === Tag operations ===

    async def get_file_tags(self, file_id: int) -> list[str]:
        return await self._get_list(f"/files/{file_id}/tags", TagRecord)

    async def add_tags(self, file_id: int, tags: list[str]) -> list[str]:
        return await self._request_json(
            "POST", f"/files/{file_id}/tags", json=tags
        )

    async def remove_tags(self, file_id: int, tags: list[str]) -> list[str]:
        return await self._request_json(
            "DELETE", f"/files/{file_id}/tags", json=tags
        )

    async def read_file_content(self, file_id: int) -> dict:
        """Read text content of a file by ID.

        Returns a dict with: file_id, filename, file_path, content, is_binary, truncated.
        """
        return await self._request_json("GET", f"/files/{file_id}/content")

    async def get_user_tags(self, user_id: int) -> list[str]:
        """Get all unique tags used by a user across their files."""
        return await self._request_json("GET", f"/files/user/{user_id}/tags")

    async def search_files_by_tag(self, user_id: int, tag: str) -> dict:
        """Find all files for a user that have a specific tag.

        Returns a dict with: files (list of file records with tags), tag, message.
        """
        return await self._request_json(
            "GET", f"/files/user/{user_id}/search", params={"tag": tag}
        )
