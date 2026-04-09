"""Typed response models for the file tagging & retrieval system."""

from datetime import datetime

from pydantic import BaseModel


class FileRecord(BaseModel):
    id: int | None = None
    user_id: int
    file_path: str
    created_at: datetime | None = None


class TagRecord(BaseModel):
    id: int | None = None
    name: str


class FileWithTag(BaseModel):
    file: FileRecord
    tags: list[str]
