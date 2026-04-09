"""Models for users (Telegram users)."""

from sqlmodel import Field, SQLModel


class UserRecord(SQLModel, table=True):
    """A row in the users table."""

    __tablename__ = "user"

    id: int = Field(primary_key=True)  # Telegram user ID
    username: str = ""


class UserCreate(SQLModel):
    """Schema for creating a user."""

    id: int
    username: str = ""
