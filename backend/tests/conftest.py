import os

# Isolated in-memory database and test-only keys; never read or mutate a user's DB.
os.environ['DB_DRIVER'] = 'sqlite+aiosqlite'
os.environ['DB_NAME'] = ':memory:'
os.environ['JWT_SECRET_KEY'] = 'test-only-key-never-use-in-deployment-123456789'
os.environ['COOKIE_SECURE'] = 'false'
os.environ['GEMINI_API_KEY'] = ''
os.environ['MAIL_MODE'] = 'disabled'
os.environ['LLM_PROVIDER'] = 'gemini'
os.environ['LLM_MODEL'] = 'gemini-3.5-flash-lite'

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.core import get_db
from app.main import app
from app.models import Base

@pytest_asyncio.fixture
async def database():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:', poolclass=StaticPool)
    @event.listens_for(engine.sync_engine, 'connect')
    def foreign_keys(connection, _record):
        connection.execute('PRAGMA foreign_keys=ON')
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async def override():
        async with sessions() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    app.dependency_overrides[get_db] = override
    yield sessions
    app.dependency_overrides.clear()
    await engine.dispose()

@pytest_asyncio.fixture
async def client(database):
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as client:
        yield client

async def register(client, username='alice'):
    payload = {'username': username, 'email': f'{username}@example.com', 'password': 'Bridge-Test-42!', 'display_name': username.title()}
    response = await client.post('/api/v1/auth/signup', json=payload)
    assert response.status_code == 201, response.text
    response = await client.post('/api/v1/auth/login', json={'email': payload['email'], 'password': payload['password']})
    assert response.status_code == 200, response.text
    return response.json()

@pytest_asyncio.fixture
async def account(client):
    return await register(client)
