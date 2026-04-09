"""Models for user files."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class FileRecord(SQLModel, table=True):
    """A row in the files table."""

    __tablename__ = "file"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    file_path: str = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )


class FileCreate(SQLModel):
    """Schema for creating a file record."""

    user_id: int
    file_path: str


class FileRead(SQLModel):
    """Schema for reading a file record."""

    id: int
    user_id: int
    file_path: str
    created_at: datetime
