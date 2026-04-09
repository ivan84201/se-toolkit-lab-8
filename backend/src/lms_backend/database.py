"""Database connection management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.settings import settings

# Import models so they register their tables with SQLModel metadata
from lms_backend.models.file import FileRecord  # noqa: F401
from lms_backend.models.file_tag import FileTagRecord  # noqa: F401
from lms_backend.models.tag import TagRecord  # noqa: F401
from lms_backend.models.user import UserRecord  # noqa: F401


def get_database_url() -> str:
    return (
        f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )


engine = create_async_engine(get_database_url())


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(engine) as session:
        yield session
