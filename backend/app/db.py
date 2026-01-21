"""Database connection and session management."""
import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.models.database import Base

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://adventure:development_password@localhost:5432/adventure_engine")

# Convert to async URL (asyncpg driver)
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Create async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    poolclass=NullPool,  # Disable connection pooling for development
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Initialize database tables (create all tables)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """Drop all database tables (use with caution!)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Usage:
        async with get_db() as session:
            result = await session.execute(select(Character))
            characters = result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """
    Dependency for FastAPI endpoints.

    Usage in FastAPI:
        @app.get("/characters")
        async def list_characters(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Character))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for convenience
get_db = get_db_session
