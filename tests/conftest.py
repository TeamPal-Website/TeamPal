import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
import sqlalchemy.dialects.postgresql as _pg
from sqlalchemy import JSON as _JSON
_pg.JSONB = _JSON
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from src.database import Base
import src.models.skills
import src.models.projects
import src.models.roles_dictionary
from src.main import app
from tests.common import COMPLETE_PROFILE_JSON
test_engine = create_async_engine('sqlite+aiosqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
test_async_session_maker = async_sessionmaker(bind=test_engine, expire_on_commit=False)

@event.listens_for(test_engine.sync_engine, 'connect')
def _sqlite_enable_foreign_keys(dbapi_connection, _connection_record):
    if test_engine.sync_engine.dialect.name == 'sqlite':
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()

@pytest.fixture(autouse=True)
def _stub_catalog_invalidate_schedule(monkeypatch):
    monkeypatch.setattr('src.catalog_cache.schedule_catalog_invalidate', lambda names: None)

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
    with patch('src.api.dependencies.async_session_maker', test_async_session_maker):
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            yield ac

@pytest.fixture
async def registered_user(client: AsyncClient):
    user_data = {'email': 'test@example.com', 'password': 'password123'}
    await client.post('/auth/register', json=user_data)
    return user_data

@pytest.fixture
async def auth_token(client: AsyncClient, registered_user: dict):
    response = await client.post('/auth/login', json=registered_user)
    return response.json()['access_token']

async def complete_profile_minimal(ac: AsyncClient) -> None:
    r = await ac.patch('/profiles', json=COMPLETE_PROFILE_JSON)
    assert r.status_code == 200, r.text

@pytest.fixture
async def authenticated_client(client: AsyncClient, auth_token: str):
    client.cookies.set('access_token', auth_token)
    await complete_profile_minimal(client)
    return client

@pytest.fixture
async def city(client: AsyncClient):
    response = await client.post('/cities', json={'title': 'Москва'})
    return response.json()['data']

@pytest.fixture
async def user_id(authenticated_client: AsyncClient):
    response = await authenticated_client.get('/auth/me')
    return response.json()['id']

@pytest.fixture
async def role_id(client: AsyncClient):
    response = await client.post('/roles_dictionary', json={'name': 'Разработчик'})
    return response.json()['data']['id']

@pytest.fixture
async def skill_id(client: AsyncClient):
    response = await client.post('/skills', json={'name': 'Python'})
    return response.json()['data']['id']
