"""Canonical package for the LMS MCP server."""

from mcp_lms.client import LMSClient
from mcp_lms.models import FileRecord, FileWithTag, TagRecord
from mcp_lms.settings import Settings
from mcp_lms.server import create_server, main

__all__ = [
    "FileRecord",
    "FileWithTag",
    "LMSClient",
    "Settings",
    "TagRecord",
    "create_server",
    "main",
]
