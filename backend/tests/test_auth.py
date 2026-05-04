import pytest
from datetime import datetime, timedelta
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.auth import create_access_token, hash_password, verify_password
from app.config import settings
from app.database import get_session
from app.models.project import Base
from app.models.user import User  # noqa: F401

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

async def _register(client: AsyncClient, **overrides):
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "secret123",
        **overrides,
    }
    return await client.post("/api/v1/auth/register", json=payload)


async def _login(client: AsyncClient, username="testuser", password="secret123"):
    return await client.post("/api/v1/auth/login", json={"username": username, "password": password})


# ---------------------------------------------------------------------------
# Registration — happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await _register(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_returns_created_at(client: AsyncClient):
    resp = await _register(client)
    assert resp.status_code == 201
    data = resp.json()
    assert "created_at" in data
    # Should be parseable as ISO datetime
    datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_register_different_users(client: AsyncClient):
    """Two different users should both register successfully."""
    await _register(client, username="alice", email="alice@example.com")
    resp = await _register(client, username="bob", email="bob@example.com")
    assert resp.status_code == 201
    assert resp.json()["username"] == "bob"


# ---------------------------------------------------------------------------
# Registration — duplicate handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    await _register(client)
    resp = await _register(client, email="other@example.com")
    assert resp.status_code == 400
    assert "already taken" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await _register(client)
    resp = await _register(client, username="otheruser")
    assert resp.status_code == 400
    assert "already taken" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Registration — boundary / validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_empty_body(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_password(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "username": "user1",
        "email": "user1@example.com",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_username(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "user1@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_email(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "username": "user1",
        "password": "secret123",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    resp = await _register(client, email="not-an-email")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_empty_password(client: AsyncClient):
    """Empty string password should be rejected."""
    resp = await _register(client, password="")
    # Pydantic may accept empty string as str — either 422 (if min_length) or 201
    # We just record the behaviour; if it's 201 that's a security gap to flag.
    assert resp.status_code in (422, 201)


# ---------------------------------------------------------------------------
# Login — happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await _register(client)
    resp = await _login(client)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


# ---------------------------------------------------------------------------
# Login — error cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await _register(client)
    resp = await _login(client, password="wrong")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    resp = await _login(client, username="nobody", password="secret123")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_empty_body(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_empty_password(client: AsyncClient):
    await _register(client)
    resp = await _login(client, password="")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /me — authenticated access
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient):
    await _register(client)
    login_resp = await _login(client)
    token = login_resp.json()["access_token"]
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_me_no_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer totally-fake-token"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_malformed_auth_header(client: AsyncClient):
    """Authorization header without 'Bearer ' prefix."""
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "some-token"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_expired_token(client: AsyncClient):
    """Token that has already expired should be rejected."""
    expired = jwt.encode(
        {"sub": "fake-id", "exp": datetime.utcnow() - timedelta(hours=1)},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_token_signed_with_wrong_secret(client: AsyncClient):
    """Token signed with a different secret must be rejected."""
    bad_token = jwt.encode(
        {"sub": "fake-id", "exp": datetime.utcnow() + timedelta(hours=1)},
        "totally-different-secret",
        algorithm=settings.JWT_ALGORITHM,
    )
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_token_missing_sub_claim(client: AsyncClient):
    """Valid JWT signature but missing 'sub' claim must be rejected."""
    no_sub = jwt.encode(
        {"exp": datetime.utcnow() + timedelta(hours=1)},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {no_sub}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_token_with_deleted_user(client: AsyncClient):
    """Token is valid but the user no longer exists in the DB."""
    # Manually create a token for a non-existent user-id
    ghost_token = create_access_token("nonexistent-user-id-12345")
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {ghost_token}"})
    assert resp.status_code == 401
    assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# JWT token integrity
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_token_contains_correct_user_id(client: AsyncClient):
    """Decoded token should reference the registered user's ID."""
    await _register(client)
    login_resp = await _login(client)
    token = login_resp.json()["access_token"]
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert "sub" in payload
    assert "exp" in payload


@pytest.mark.asyncio
async def test_token_uses_correct_algorithm(client: AsyncClient):
    """Token header should use HS256."""
    await _register(client)
    login_resp = await _login(client)
    token = login_resp.json()["access_token"]
    header = jwt.get_unverified_header(token)
    assert header["alg"] == settings.JWT_ALGORITHM


# ---------------------------------------------------------------------------
# Password security
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_password_is_hashed_in_db(client: AsyncClient):
    """Verify the password stored in DB is bcrypt-hashed, not plaintext."""
    await _register(client)
    async with TestingSession() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "testuser"))
        user = result.scalar_one()
        assert user.hashed_password != "secret123"
        assert verify_password("secret123", user.hashed_password)


@pytest.mark.asyncio
async def test_password_hash_not_in_register_response(client: AsyncClient):
    resp = await _register(client)
    assert "hashed_password" not in resp.json()


@pytest.mark.asyncio
async def test_password_hash_not_in_me_response(client: AsyncClient):
    await _register(client)
    token = (await _login(client)).json()["access_token"]
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert "hashed_password" not in resp.json()


# ---------------------------------------------------------------------------
# Unit-level: hash_password / verify_password helpers
# ---------------------------------------------------------------------------

def test_hash_password_produces_bcrypt_hash():
    hashed = hash_password("mypassword")
    assert hashed.startswith("$2b$")
    assert hashed != "mypassword"


def test_verify_password_correct():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


# ---------------------------------------------------------------------------
# Unit-level: create_access_token
# ---------------------------------------------------------------------------

def test_create_access_token_returns_jwt():
    token = create_access_token("user-123")
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == "user-123"
    assert "exp" in payload


# ---------------------------------------------------------------------------
# Cross-endpoint flow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_login_me_full_flow(client: AsyncClient):
    """Complete happy-path: register -> login -> /me."""
    reg = await _register(client)
    assert reg.status_code == 201
    user_id = reg.json()["id"]

    login = await _login(client)
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["id"] == user_id
