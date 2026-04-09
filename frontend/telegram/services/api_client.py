"""HTTP client for the backend file tagging API."""

import logging
from pathlib import Path

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


class FileNotFoundError_(APIError):
    """Raised when the backend returns 404 — resource not found."""

    def __init__(self, message: str) -> None:
        super().__init__(404, message)


class DuplicateFileError(APIError):
    """Raised when the backend returns 409 — file with same name exists."""

    def __init__(self, message: str) -> None:
        super().__init__(409, message)


class ServerError(APIError):
    """Raised when the backend returns 5xx — internal server error."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(status_code, message)


class ClientError(APIError):
    """Raised when the backend returns 4xx (not 404 or 409) — bad request / auth failure."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(status_code, message)


def _raise_for_response(response: httpx.Response) -> None:
    """Convert an httpx response with an error status into a specific APIError."""
    if response.status_code == 404:
        detail = response.json().get("detail", "Resource not found") if response.headers.get("content-type", "").startswith("application/json") else "Resource not found"
        raise FileNotFoundError_(detail)
    if response.status_code == 409:
        detail = response.json().get("detail", "Duplicate resource") if response.headers.get("content-type", "").startswith("application/json") else "Duplicate resource"
        raise DuplicateFileError(detail)
    if 400 <= response.status_code < 500:
        detail = response.json().get("detail", "Client error") if response.headers.get("content-type", "").startswith("application/json") else "Client error"
        raise ClientError(response.status_code, detail)
    if response.status_code >= 500:
        detail = response.json().get("detail", "Server error") if response.headers.get("content-type", "").startswith("application/json") else "Server error"
        raise ServerError(response.status_code, detail)


class FileInfo(BaseModel):
    id: int
    user_id: int
    file_path: str
    created_at: str


class APIClient:
    """Calls the backend API for file/tag operations."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def upload_file(
        self, user_id: int, file_path: str, tags: list[str] | None = None
    ) -> FileInfo:
        """Upload a local file to the backend.

        file_path is a local filesystem path the bot can read.
        """
        local = Path(file_path)
        if not local.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        params: dict[str, object] = {"user_id": user_id}
        if tags:
            params["tags"] = ",".join(tags)

        response = await self._client.post(
            "/files/",
            params=params,
            files={"file": (local.name, local.read_bytes(), "application/octet-stream")},
        )
        if response.is_error:
            _raise_for_response(response)
        return FileInfo.model_validate(response.json())

    async def get_user_files(self, user_id: int) -> list[FileInfo]:
        response = await self._client.get(f"/files/user/{user_id}")
        if response.is_error:
            _raise_for_response(response)
        return [FileInfo.model_validate(item) for item in response.json()]

    async def delete_file(self, file_id: int, user_id: int) -> None:
        response = await self._client.delete(
            f"/files/{file_id}",
            params={"user_id": user_id},
        )
        if response.is_error:
            _raise_for_response(response)

    async def get_file_tags(self, file_id: int) -> list[str]:
        response = await self._client.get(f"/files/{file_id}/tags")
        if response.is_error:
            _raise_for_response(response)
        return response.json()

    async def add_tags(self, file_id: int, tags: list[str]) -> list[str]:
        response = await self._client.post(f"/files/{file_id}/tags", json=tags)
        if response.is_error:
            _raise_for_response(response)
        return response.json()

    async def remove_tags(self, file_id: int, tags: list[str]) -> list[str]:
        response = await self._client.request("DELETE", f"/files/{file_id}/tags", json=tags)
        if response.is_error:
            _raise_for_response(response)
        return response.json()

    async def get_file_by_name(self, user_id: int, filename: str) -> int:
        """Find a file ID by filename. Returns the file ID."""
        response = await self._client.get(
            f"/files/user/{user_id}/find",
            params={"filename": filename},
        )
        if response.is_error:
            _raise_for_response(response)
        return response.json()["file_id"]

    async def download_file(self, file_id: int) -> bytes:
        """Download a file's raw bytes by its ID."""
        response = await self._client.get(f"/files/{file_id}/download")
        if response.is_error:
            _raise_for_response(response)
        return response.content
