"""Tool schemas, handlers, and registry for the observability MCP server."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from mcp.types import Tool
from pydantic import BaseModel, Field

from mcp_obs.client import ObsClient


class NoArgs(BaseModel):
    """Empty input model for tools that only need server-side configuration."""


class LogsSearchQuery(BaseModel):
    query: str = Field(
        description="LogsQL query string, e.g., '_time:10m service.name:\"Learning Management Service\" severity:ERROR'"
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Max log entries to return (default 100)."
    )


class LogsErrorCountQuery(BaseModel):
    service: str | None = Field(
        default=None, description="Optional service name to filter errors."
    )
    time_range: str = Field(
        default="1h", description="Time window for error count (default 1h)."
    )


class TracesListQuery(BaseModel):
    service: str | None = Field(
        default=None, description="Optional service name to filter traces."
    )
    limit: int = Field(
        default=20, ge=1, le=100, description="Max traces to return (default 20)."
    )


class TracesGetQuery(BaseModel):
    trace_id: str = Field(description="Trace ID to fetch.")


ToolPayload = BaseModel | Sequence[BaseModel]
ToolHandler = Callable[[ObsClient, BaseModel], Awaitable[ToolPayload]]


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


async def _logs_search(client: ObsClient, args: BaseModel) -> ToolPayload:
    query = args if isinstance(args, LogsSearchQuery) else None
    if query is None:
        raise TypeError(f"Expected {LogsSearchQuery.__name__}, got {type(args).__name__}")
    return await client.logs_search(query.query, query.limit)


async def _logs_error_count(client: ObsClient, args: BaseModel) -> ToolPayload:
    query = args if isinstance(args, LogsErrorCountQuery) else None
    if query is None:
        raise TypeError(f"Expected {LogsErrorCountQuery.__name__}, got {type(args).__name__}")
    return await client.logs_error_count(query.service, query.time_range)


async def _traces_list(client: ObsClient, args: BaseModel) -> ToolPayload:
    query = args if isinstance(args, TracesListQuery) else None
    if query is None:
        raise TypeError(f"Expected {TracesListQuery.__name__}, got {type(args).__name__}")
    return await client.traces_list(query.service, query.limit)


async def _traces_get(client: ObsClient, args: BaseModel) -> ToolPayload:
    query = args if isinstance(args, TracesGetQuery) else None
    if query is None:
        raise TypeError(f"Expected {TracesGetQuery.__name__}, got {type(args).__name__}")
    return await client.traces_get(query.trace_id)


TOOL_SPECS = (
    ToolSpec(
        "logs_search",
        "Search logs by keyword and/or time range using LogsQL.",
        LogsSearchQuery,
        _logs_search,
    ),
    ToolSpec(
        "logs_error_count",
        "Count errors per service over a time window.",
        LogsErrorCountQuery,
        _logs_error_count,
    ),
    ToolSpec(
        "traces_list",
        "List recent traces, optionally filtered by service.",
        TracesListQuery,
        _traces_list,
    ),
    ToolSpec(
        "traces_get",
        "Fetch a specific trace by ID.",
        TracesGetQuery,
        _traces_get,
    ),
)
TOOLS_BY_NAME = {spec.name: spec for spec in TOOL_SPECS}
