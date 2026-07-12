# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Test fixtures for cloud API integration tests.
Sets up TestClient, mocks JWT auth, and mocks the database layer.
"""
import os
import pytest
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Set a test secret before importing app so auth middleware can instantiate
os.environ.setdefault("NEXTAUTH_SECRET", "test-secret-for-testing-only")

from src.main import app  # noqa: E402 — must import after env setup


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def client() -> Generator:
    """FastAPI TestClient — synchronous wrapper for quick tests."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Async HTTP client for endpoint testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def mock_auth(mocker):
    """
    Mock JWT token verification so tests don't need real tokens.
    """
    mock = mocker.patch("src.api.auth_middleware.verify_auth_token")
    mock.return_value = {
        "user_id": "1",
        "email": "test@example.com",
    }
    return mock


@pytest.fixture(autouse=True)
def mock_db_service(mocker):
    """
    Mock the database service for all tests to avoid needing a real CockroachDB.
    Patches both fetchrow and execute on the global db_service instance.
    """
    fetchrow_mock = mocker.patch("src.services.db_service.db_service.fetchrow")
    fetchrow_mock.return_value = {"files": []}

    execute_mock = mocker.patch("src.services.db_service.db_service.execute")

    return {
        "fetchrow": fetchrow_mock,
        "execute": execute_mock,
    }

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
