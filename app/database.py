from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from sqlalchemy.orm import sessionmaker
import os

# DATABASE_URL = os.environ.get("DB_CONNECTION_STRING")
DATABASE_URL = "postgresql+asyncpg://asilbek:Asilbek2001@localhost/panda_profile"
engine = create_async_engine(DATABASE_URL, pool_size=20, max_overflow=30)


SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db():
    async with SessionLocal() as session:
        yield session
