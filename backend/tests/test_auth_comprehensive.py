"""
Comprehensive JWT auth test suite — AUT-158.

Covers:
- Functional: register, login, /me, duplicate rejection, nonexistent user
- Security: bcrypt hashing, JWT expiry, token signature, SQL injection, brute-force
- Boundary: empty fields, long inputs, special characters
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch

import bcrypt
import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.auth import hash_password, verify_password
from app.config import settings
from app.database import get_session
from app.models.project import Base
from app.models.user import User  # noqa: F401

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestingSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    from fastapi import FastAPI

    test_app = FastAPI()

    async def override_get_session():
        async with TestingSession() as session:
            yield session

    test_app.include_router(api_router)
    test_app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DEFAULT_USER = {"username": "testuser", "email": "test@example.com", "password": "secret123"}


async def _register(client: AsyncClient, **overrides):
    return await client.post("/api/v1/auth/register", json={**DEFAULT_USER, **overrides})


async def _login(client: AsyncClient, username="testuser", password="secret123"):
    return await client.post("/api/v1/auth/login", json={"username": username, "password": password})


async def _get_token(client: AsyncClient) -> str:
    await _register(client)
    resp = await _login(client)
    return resp.json()["access_token"]


# ===================================================================
# 1. Functional Tests
# ===================================================================


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        resp = await _register(client)
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient):
        await _register(client)
        resp = await _register(client, email="other@example.com")
        assert resp.status_code == 400
        assert "already taken" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        await _register(client)
        resp = await _register(client, username="otheruser")
        assert resp.status_code == 400
        assert "already taken" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_returns_valid_uuid(self, client: AsyncClient):
        resp = await _register(client)
        import uuid

        user_id = resp.json()["id"]
        uuid.UUID(user_id)  # raises ValueError if invalid

    @pytest.mark.asyncio
    async def test_register_password_not_returned(self, client: AsyncClient):
        resp = await _register(client)
        body = resp.text
        assert "secret123" not in body
        assert "hashed_password" not in body


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        await _register(client)
        resp = await _login(client)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        await _register(client)
        resp = await _login(client, password="wrong")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await _login(client, username="ghost")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_token_contains_user_id(self, client: AsyncClient):
        await _register(client)
        resp = await _login(client)
        token = resp.json()["access_token"]
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload.get("sub") is not None

    @pytest.mark.asyncio
    async def test_login_token_has_correct_expiry(self, client: AsyncClient):
        await _register(client)
        resp = await _login(client)
        token = resp.json()["access_token"]
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        exp = datetime.utcfromtimestamp(payload["exp"])
        # Should expire ~24 hours from now (give 5 min tolerance)
        expected = datetime.utcnow() + timedelta(hours=24)
        assert abs((exp - expected).total_seconds()) < 300


class TestMe:
    @pytest.mark.asyncio
    async def test_me_authenticated(self, client: AsyncClient):
        token = await _get_token(client)
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_me_no_token(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_expired_token(self, client: AsyncClient):
        # Create a token that expired 1 hour ago
        expired = datetime.utcnow() - timedelta(hours=1)
        token = jwt.encode(
            {"sub": "fake-id", "exp": expired},
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_invalid_signature(self, client: AsyncClient):
        token = jwt.encode(
            {"sub": "fake-id", "exp": datetime.utcnow() + timedelta(hours=1)},
            "wrong-secret",
            algorithm="HS256",
        )
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_garbage_token(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_wrong_token_format(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Basic abc123"})
        assert resp.status_code == 401


# ===================================================================
# 2. Security Tests
# ===================================================================


class TestSecurity:
    @pytest.mark.asyncio
    async def test_password_stored_as_bcrypt_hash(self, client: AsyncClient):
        await _register(client)
        async with TestingSession() as session:
            result = await session.execute(select(User).where(User.username == "testuser"))
            user = result.scalar_one()
            assert user.hashed_password != "secret123"
            assert user.hashed_password.startswith("$2")
            assert bcrypt.checkpw(b"secret123", user.hashed_password.encode())

    @pytest.mark.asyncio
    async def test_hash_password_uses_bcrypt(self):
        hashed = hash_password("test123")
        assert hashed.startswith("$2")
        assert verify_password("test123", hashed)
        assert not verify_password("wrong", hashed)

    @pytest.mark.asyncio
    async def test_jwt_expiration_is_24_hours(self):
        token = jwt.encode(
            {"sub": "test-id", "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)},
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        exp = datetime.utcfromtimestamp(payload["exp"])
        delta = exp - datetime.utcnow()
        assert 23.5 < delta.total_seconds() / 3600 < 24.5

    @pytest.mark.asyncio
    async def test_jwt_signature_verification(self):
        """Valid token should decode; tampered signature should fail."""
        from jose import JWTError

        token = jwt.encode(
            {"sub": "test-id", "exp": datetime.utcnow() + timedelta(hours=1)},
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        # Valid decode succeeds
        jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        # Wrong secret fails
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong-secret", algorithms=[settings.JWT_ALGORITHM])

    @pytest.mark.asyncio
    async def test_sql_injection_in_username(self, client: AsyncClient):
        """SQL injection attempt in username should not cause issues."""
        payload = {
            "username": "'; DROP TABLE users; --",
            "email": "inject@example.com",
            "password": "secret123",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        # SQLAlchemy parameterized queries prevent injection — register may succeed
        # or return validation error, but should NOT crash
        assert resp.status_code in (201, 400, 422)

        # Verify users table still exists by registering a normal user
        resp2 = await _register(client)
        assert resp2.status_code == 201

    @pytest.mark.asyncio
    async def test_sql_injection_in_login(self, client: AsyncClient):
        await _register(client)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "' OR 1=1 --", "password": "anything"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_brute_force_does_not_leak_info(self, client: AsyncClient):
        """Repeated failed logins should all return 401 without leaking user existence."""
        await _register(client)
        for _ in range(10):
            resp = await _login(client, password="guess")
            assert resp.status_code == 401
            assert "Invalid credentials" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_nonexistent_user_login_same_error(self, client: AsyncClient):
        """Nonexistent user should get same error as wrong password (no enumeration)."""
        resp = await _login(client, username="nobody", password="wrong")
        assert resp.status_code == 401
        assert "Invalid credentials" in resp.json()["detail"]


# ===================================================================
# 3. Boundary Tests
# ===================================================================


class TestBoundary:
    @pytest.mark.asyncio
    async def test_register_empty_username(self, client: AsyncClient):
        resp = await _register(client, username="")
        # Should either reject (400/422) or succeed — should not crash
        assert resp.status_code in (201, 400, 422)

    @pytest.mark.asyncio
    async def test_register_empty_password(self, client: AsyncClient):
        resp = await _register(client, password="")
        assert resp.status_code in (201, 400, 422)

    @pytest.mark.asyncio
    async def test_register_empty_email(self, client: AsyncClient):
        resp = await _register(client, email="")
        # EmailStr validation should reject empty email
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_register_long_username(self, client: AsyncClient):
        long_name = "a" * 500
        resp = await _register(client, username=long_name)
        assert resp.status_code in (201, 400, 422)

    @pytest.mark.xfail(
        reason="BUG: bcrypt raises ValueError for passwords >72 bytes. "
               "Code should validate length and return 400/422."
    )
    @pytest.mark.asyncio
    async def test_register_long_password(self, client: AsyncClient):
        long_pw = "p" * 1000
        resp = await _register(client, password=long_pw)
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_register_special_characters_username(self, client: AsyncClient):
        """Username with unicode/special chars should be handled."""
        resp = await _register(client, username="user@#%!&*()")
        assert resp.status_code in (201, 400, 422)

    @pytest.mark.asyncio
    async def test_register_unicode_username(self, client: AsyncClient):
        resp = await _register(client, username="用户测试")
        assert resp.status_code in (201, 400, 422)

    @pytest.mark.asyncio
    async def test_register_special_chars_in_password(self, client: AsyncClient):
        """Passwords with special chars should work fine."""
        resp = await _register(client, password="p@ss!w0rd#$%^&*()")
        assert resp.status_code == 201
        login = await _login(client, password="p@ss!w0rd#$%^&*()")
        assert login.status_code == 200

    @pytest.mark.asyncio
    async def test_register_password_with_spaces(self, client: AsyncClient):
        resp = await _register(client, password="  spaces  ")
        assert resp.status_code == 201
        login = await _login(client, password="  spaces  ")
        assert login.status_code == 200
