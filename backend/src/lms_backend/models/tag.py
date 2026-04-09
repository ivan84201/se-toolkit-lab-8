"""Models for tags."""

from sqlmodel import Field, SQLModel


class TagRecord(SQLModel, table=True):
    """A row in the tags table."""

    __tablename__ = "tag"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, nullable=False)


class TagCreate(SQLModel):
    """Schema for creating a tag."""

    name: str


class TagRead(SQLModel):
    """Schema for reading a tag."""

    id: int
    name: str
