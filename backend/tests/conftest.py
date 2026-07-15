import os

os.environ["DATABASE_URL"] = "postgresql+asyncpg://printflow:printflow@localhost:5433/printflow_test"
os.environ.setdefault("JWT_SECRET", "test-secret-nao-usar-em-producao")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:4200")

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

settings = get_settings()
engine_teste = create_async_engine(settings.database_url)
session_factory_teste = async_sessionmaker(engine_teste, expire_on_commit=False)


async def _override_get_db():
    async with session_factory_teste() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(autouse=True)
async def banco_limpo():
    async with engine_teste.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_teste.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
