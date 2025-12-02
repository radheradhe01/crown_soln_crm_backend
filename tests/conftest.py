import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import pool
from app.main import app
from app.core.database import get_db
from app.core.config import settings

@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=pool.NullPool,
        )
        async_session = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with async_session() as session:
            yield session
        await engine.dispose()

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
