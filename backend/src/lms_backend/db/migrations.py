"""Database table creation and migrations."""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from lms_backend.database import get_database_url
from lms_backend.models.file import FileRecord  # noqa: F401 - registers table
from lms_backend.models.file_tag import FileTagRecord  # noqa: F401 - registers table
from lms_backend.models.tag import TagRecord  # noqa: F401 - registers table
from lms_backend.models.user import UserRecord  # noqa: F401 - registers table

logger = logging.getLogger(__name__)


async def create_tables() -> None:
    """Create all tables defined in the models."""
    engine = create_async_engine(get_database_url())
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    await engine.dispose()
    logger.info("tables_created", extra={"event": "tables_created"})


async def run_sql_migration(session) -> None:
    """Run raw SQL migrations from schema.sql."""
    schema_path = (
        __import__("pathlib").Path(__file__).parent / "schema.sql"
    )
    if not schema_path.exists():
        logger.warning("schema_file_missing", extra={"event": "schema_file_missing"})
        return

    sql = schema_path.read_text()
    statements = [s.strip() for s in sql.split(";") if s.strip()]

    for stmt in statements:
        await session.exec(text(stmt))
    await session.commit()
    logger.info("sql_migration_completed", extra={"event": "sql_migration_completed"})
