"""
RecruitBot — Database Connection & Session Management

Provides async SQLAlchemy engine and session factory.
Used by all services to interact with PostgreSQL + pgvector.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

# ── Build the async database URL ──
# Convert postgresql:// to postgresql+asyncpg:// for async driver
DATABASE_URL = settings.DATABASE_URL or "postgresql+asyncpg://recruitbot_user:recruitbot_password@localhost:5432/recruitbot_db"
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Sync URL for Alembic migrations (uses psycopg2)
SYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

# ── Engine ──
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# ── Session Factory ──
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base class for all ORM models ──
class Base(DeclarativeBase):
    pass


# ── Dependency for FastAPI route injection ──
async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields a database session.
    Usage: db: AsyncSession = Depends(get_db)
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
