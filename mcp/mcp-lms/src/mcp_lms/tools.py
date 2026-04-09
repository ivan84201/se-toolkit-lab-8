"""Tool schemas, handlers, and registry for the LMS MCP server."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from mcp.types import Tool
from pydantic import BaseModel, Field

from mcp_lms.client import LMSClient


class NoArgs(BaseModel):
    """Empty input model for tools that only need server-side configuration."""


class FileCreateArgs(BaseModel):
    user_id: int = Field(description="Telegram user identifier.")
    file_path: str = Field(
        description="Local filesystem path to the file to upload, e.g. '/tmp/report.pdf'."
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Optional tags to attach to the file.",
    )


class FileDeleteArgs(BaseModel):
    file_id: int = Field(description="ID of the file to delete.")


class UserFilesArgs(BaseModel):
    user_id: int = Field(description="Telegram user identifier.")


class FileTagsArgs(BaseModel):
    file_id: int = Field(description="ID of the file.")


class AddTagsArgs(BaseModel):
    file_id: int = Field(description="ID of the file.")
    tags: list[str] = Field(description="Tags to attach. Will be normalized to lowercase.")


class RemoveTagsArgs(BaseModel):
    file_id: int = Field(description="ID of the file.")
    tags: list[str] = Field(description="Tags to remove.")


class ReadFileContentArgs(BaseModel):
    file_id: int = Field(
        description="ID of the file to read. Use the returned file_path with the exec tool to read content."
    )


class GetUserTagsArgs(BaseModel):
    user_id: int = Field(description="Telegram user identifier.")


class SearchFilesByTagArgs(BaseModel):
    user_id: int = Field(description="Telegram user identifier.")
    tag: str = Field(description="Tag name to search for (case-insensitive).")


ToolPayload = BaseModel | Sequence[BaseModel]
ToolHandler = Callable[[LMSClient, BaseModel], Awaitable[ToolPayload]]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    model: type[BaseModel]
    handler: ToolHandler

    def as_tool(self) -> Tool:
        schema = self.model.model_json_schema()
        schema.pop("$defs", None)
        schema.pop("title", None)
        return Tool(name=self.name, description=self.description, inputSchema=schema)


async def _add_file(client: LMSClient, args: FileCreateArgs) -> ToolPayload:
    return await client.add_file(args.user_id, args.file_path, args.tags)


async def _delete_file(client: LMSClient, args: FileDeleteArgs) -> ToolPayload:
    return await client.delete_file(args.file_id)


async def _get_user_files(client: LMSClient, args: UserFilesArgs) -> ToolPayload:
    return await client.get_user_files(args.user_id)


async def _get_file_tags(client: LMSClient, args: FileTagsArgs) -> ToolPayload:
    return await client.get_file_tags(args.file_id)


async def _add_tags(client: LMSClient, args: AddTagsArgs) -> ToolPayload:
    return await client.add_tags(args.file_id, args.tags)


async def _remove_tags(client: LMSClient, args: RemoveTagsArgs) -> ToolPayload:
    return await client.remove_tags(args.file_id, args.tags)


async def _read_file_content(client: LMSClient, args: ReadFileContentArgs) -> ToolPayload:
    """Return file metadata and the full filesystem path for reading via exec tool."""
    result = await client.read_file_content(args.file_id)
    # result contains: file_id, filename, file_path, content, is_binary, truncated
    # Construct the full path inside nanobot container where files are mounted
    # Files are mounted at /app/nanobot/workspace/files/<user_id>/<filename>
    # The file_path from backend is relative (e.g. "123/report.pdf")
    file_path_relative = result.get("file_path", "")
    full_path = f"/app/nanobot/workspace/files/{file_path_relative}"
    return {
        "file_id": result.get("file_id", args.file_id),
        "filename": result.get("filename", "unknown"),
        "file_path": full_path,
        "is_binary": result.get("is_binary", False),
        "truncated": result.get("truncated", False),
        "message": (
            f"File is available at path: {full_path}. "
            f"Use the exec tool to read it: `cat {full_path}` for text files, "
            f"`head {full_path}` for preview, or `strings {full_path}` for binary/PDF files."
        ),
    }


async def _get_user_tags(client: LMSClient, args: GetUserTagsArgs) -> ToolPayload:
    return await client.get_user_tags(args.user_id)


async def _search_files_by_tag(
    client: LMSClient, args: SearchFilesByTagArgs
) -> ToolPayload:
    return await client.search_files_by_tag(args.user_id, args.tag)


TOOL_SPECS = (
    ToolSpec(
        "add_file",
        "Upload a file from the local filesystem to the user's storage. "
        "The file is stored at files/<user_id>/<filename> on the server. "
        "Use when a user uploads or references a file. "
        "`file_path` must be a readable local filesystem path.",
        FileCreateArgs,
        _add_file,
    ),
    ToolSpec(
        "delete_file",
        "Delete a file record and all its attached tags.",
        FileDeleteArgs,
        _delete_file,
    ),
    ToolSpec(
        "get_user_files",
        "List all files uploaded by a specific user.",
        UserFilesArgs,
        _get_user_files,
    ),
    ToolSpec(
        "get_file_tags",
        "Get all tags attached to a specific file.",
        FileTagsArgs,
        _get_file_tags,
    ),
    ToolSpec(
        "add_tags",
        "Attach tags to an existing file. Tags are normalized to lowercase and deduplicated.",
        AddTagsArgs,
        _add_tags,
    ),
    ToolSpec(
        "remove_tags",
        "Remove specific tags from a file. No error if tags don't exist.",
        RemoveTagsArgs,
        _remove_tags,
    ),
    ToolSpec(
        "read_file_content",
        "Get the filesystem path of a file so you can read its content. "
        "Returns the full path inside the nanobot container (e.g. /app/nanobot/workspace/files/123/report.pdf). "
        "After calling this, use the exec tool to read the file: "
        "`cat <path>` for text files, `head <path>` for preview, "
        "`strings <path>` for binary/PDF files to extract readable text. "
        "This works for ALL file types including PDFs.",
        ReadFileContentArgs,
        _read_file_content,
    ),
    ToolSpec(
        "get_user_tags",
        "List all unique tags used by a specific user across all their files. "
        "Call this FIRST to see what tags exist before searching. "
        "Returns a flat list of tag name strings.",
        GetUserTagsArgs,
        _get_user_tags,
    ),
    ToolSpec(
        "search_files_by_tag",
        "Find all files for a user that have a specific tag. "
        "Returns file records with their tags. "
        "Use this after get_user_tags to find files matching a topic. "
        "Use get_user_tags first to discover available tags.",
        SearchFilesByTagArgs,
        _search_files_by_tag,
    ),
)
TOOLS_BY_NAME = {spec.name: spec for spec in TOOL_SPECS}
