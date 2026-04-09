"""Models for file-tag relationships (many-to-many)."""

from sqlmodel import Field, SQLModel


class FileTagRecord(SQLModel, table=True):
    """A row in the file_tags table (many-to-many relationship)."""

    __tablename__ = "file_tag"

    file_id: int = Field(foreign_key="file.id", nullable=False, primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", nullable=False, primary_key=True)
