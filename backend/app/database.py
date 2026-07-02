from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

# Create async engine for MySQL connections
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True if database query logging is needed
    pool_pre_ping=True
)

# Async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base model for tables mapping
Base = declarative_base()

# Dependency injector yielding database session
async def get_db():
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
