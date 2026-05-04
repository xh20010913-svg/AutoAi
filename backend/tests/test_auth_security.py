"""JWT authentication security tests for AutoAi backend.

Covers: unauthenticated access, expired/forged tokens, password hashing,
duplicate registration, login error messages, and CORS configuration.
"""

import time
from datetime import datetime, timedelta

import bcrypt
import jwt as pyjwt
import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.config import settings
from app.database import get_session
from app.models.project import Base
from app.models.user import User  # noqa: F401

from sqlalchemy.pool import StaticPool

engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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


# ── helpers ──────────────────────────────────────────────────────────────────

async def _register(client: AsyncClient, **overrides):
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "secret123",
        **overrides,
    }
    return await client.post("/api/v1/auth/register", json=payload)


async def _login(client: AsyncClient, username="testuser", password="secret123"):
    return await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )


async def _get_token(client: AsyncClient, **login_kwargs) -> str:
    await _register(client, **login_kwargs.pop("register_kwargs", {}))
    resp = await _login(client, **login_kwargs)
    return resp.json()["access_token"]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Unauthenticated access to protected endpoints → 401
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_protected_me_no_token(client: AsyncClient):
    """GET /auth/me without any token must return 401."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_me_empty_bearer(client: AsyncClient):
    """GET /auth/me with empty Bearer token must return 401."""
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer "},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_me_wrong_scheme(client: AsyncClient):
    """GET /auth/me with wrong auth scheme must return 401."""
    token = await _get_token(client)
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Basic {token}"},
    )
    assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Expired token rejection
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_expired_token_rejected(client: AsyncClient):
    """A token with exp in the past must be rejected with 401."""
    await _register(client)
    # Manually craft an expired token
    expired = jwt.encode(
        {"sub": "fake-user-id", "exp": datetime.utcnow() - timedelta(hours=1)},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Forged / tampered token rejection
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_forged_token_wrong_secret(client: AsyncClient):
    """A token signed with a different secret must be rejected."""
    forged = jwt.encode(
        {"sub": "fake-user-id", "exp": datetime.utcnow() + timedelta(hours=1)},
        "totally-wrong-secret-key",
        algorithm=settings.JWT_ALGORITHM,
    )
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_tampered_token_payload(client: AsyncClient):
    """A token with modified payload (different sub) must be rejected if
    the signature no longer matches."""
    token = await _get_token(client)
    # Decode without verification, change sub, re-encode with wrong key
    payload = jwt.get_unverified_claims(token)
    payload["sub"] = "injected-user-id"
    tampered = jwt.encode(payload, "wrong-key", algorithm=settings.JWT_ALGORITHM)
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered}"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_garbage_token_string(client: AsyncClient):
    """A random string as Bearer token must be rejected."""
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-jwt-token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_token_with_wrong_algorithm(client: AsyncClient):
    """A token using a different algorithm (e.g. HS384) must be rejected."""
    forged = jwt.encode(
        {"sub": "fake-user-id", "exp": datetime.utcnow() + timedelta(hours=1)},
        settings.JWT_SECRET,
        algorithm="HS384",
    )
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Password hashing — must not store plaintext
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_password_is_hashed(client: AsyncClient):
    """The stored password must be a bcrypt hash, not plaintext."""
    await _register(client, username="hashtest", email="hash@test.com")

    # Login to verify the user was actually created with proper hashing
    login_resp = await _login(client, username="hashtest")
    assert login_resp.status_code == 200, "Login should work, proving password was stored correctly"

    # Verify via DB directly
    async with TestingSession() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "hashtest"))
        user = result.scalar_one()

    # Must not store plaintext
    assert user.hashed_password != "secret123"
    # Must start with bcrypt prefix
    assert user.hashed_password.startswith("$2b$") or user.hashed_password.startswith("$2a$")
    # Verify bcrypt can validate it
    assert bcrypt.checkpw(b"secret123", user.hashed_password.encode())
    # Wrong password must fail
    assert not bcrypt.checkpw(b"wrongpassword", user.hashed_password.encode())


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Duplicate username / email registration → 400
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_duplicate_username_rejected(client: AsyncClient):
    """Registering with an existing username must return 400."""
    await _register(client)
    resp = await _register(client, email="other@example.com")
    assert resp.status_code == 400
    assert "already taken" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_duplicate_email_rejected(client: AsyncClient):
    """Registering with an existing email must return 400."""
    await _register(client)
    resp = await _register(client, username="otheruser")
    assert resp.status_code == 400
    assert "already taken" in resp.json()["detail"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Login error messages — must not reveal whether user exists
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_login_nonexistent_user_message(client: AsyncClient):
    """Login with a non-existent username must use generic error message."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "ghost_user_that_does_not_exist", "password": "anything"},
    )
    assert resp.status_code == 401
    detail = resp.json()["detail"]
    # Must not say "user not found" or "username does not exist"
    assert "user" not in detail.lower() or "not found" not in detail.lower()
    # Should use generic message
    assert "invalid" in detail.lower()


@pytest.mark.asyncio
async def test_login_wrong_password_same_message(client: AsyncClient):
    """Login with wrong password must use the same generic message as
    a non-existent user — no timing or message difference."""
    await _register(client)

    resp_wrong_pw = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "wrong_password"},
    )
    resp_no_user = await client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent_user", "password": "anything"},
    )

    # Both return 401 with the same message
    assert resp_wrong_pw.status_code == 401
    assert resp_no_user.status_code == 401
    assert resp_wrong_pw.json()["detail"] == resp_no_user.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════════
# 7. CORS configuration — must not be wildcard with credentials
# ═══════════════════════════════════════════════════════════════════════════════


def test_cors_not_wildcard_with_credentials():
    """CORS allow_origins=['*'] with allow_credentials=True is a security risk.
    Browsers should reject this, but the server should not configure it."""
    from app.main import app

    cors_middleware = None
    for middleware in app.user_middleware:
        if middleware.cls.__name__ == "CORSMiddleware":
            cors_middleware = middleware
            break

    assert cors_middleware is not None, "CORSMiddleware not found"
    kwargs = cors_middleware.kwargs
    origins = kwargs.get("allow_origins", [])
    credentials = kwargs.get("allow_credentials", False)

    # Wildcard + credentials is insecure
    if origins == ["*"]:
        assert not credentials, (
            "CORS: allow_origins=['*'] with allow_credentials=True is insecure. "
            "Either specify explicit origins or disable credentials."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Token contains no sensitive data (password leak check)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_token_payload_no_password(client: AsyncClient):
    """JWT payload must not contain the password or password hash."""
    token = await _get_token(client)
    payload = jwt.get_unverified_claims(token)
    payload_str = str(payload).lower()
    assert "password" not in payload_str
    assert "secret123" not in payload_str
    assert "hashed_password" not in payload_str


@pytest.mark.asyncio
async def test_register_response_no_password(client: AsyncClient):
    """Registration response must not expose password or hash."""
    resp = await _register(client)
    data = resp.json()
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_me_response_no_password(client: AsyncClient):
    """GET /auth/me response must not expose password or hash."""
    token = await _get_token(client)
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = resp.json()
    assert "password" not in data
    assert "hashed_password" not in data


# ═══════════════════════════════════════════════════════════════════════════════
# 9. JWT default secret — must not use factory default in tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_jwt_secret_not_factory_default():
    """The JWT secret must not be the factory default 'change-me-in-production'.
    This test documents the issue; it will FAIL until the secret is changed."""
    assert settings.JWT_SECRET != "change-me-in-production", (
        "JWT_SECRET is still the factory default. "
        "Set a strong random secret via environment variable."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Token for deleted user → 401
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_token_for_deleted_user_rejected(client: AsyncClient):
    """A valid token for a user that was deleted from the DB must be rejected."""
    token = await _get_token(client)

    # Delete the user directly from DB
    async with TestingSession() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "testuser"))
        user = result.scalar_one()
        await session.delete(user)
        await session.commit()

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401
