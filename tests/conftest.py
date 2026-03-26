import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest
from unittest.mock import patch

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base
from src.main import app

test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
test_async_session_maker = async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with test_async_session_maker() as session:
        yield session


@pytest.fixture
async def client():
    with patch("src.api.dependencies.async_session_maker", test_async_session_maker):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac


@pytest.fixture
async def registered_user(client: AsyncClient):
    user_data = {"email": "test@example.com", "password": "password123"}
    await client.post("/auth/register", json=user_data)
    return user_data


@pytest.fixture
async def auth_token(client: AsyncClient, registered_user: dict):
    response = await client.post("/auth/login", json=registered_user)
    return response.json()["access_token"]


@pytest.fixture
async def authenticated_client(client: AsyncClient, auth_token: str):
    client.cookies.set("access_token", auth_token)
    return client
