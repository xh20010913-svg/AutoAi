import pytest
from httpx import AsyncClient
from jose import jwt

from app.config import settings
from tests.conftest import get_auth_headers, login_user, register_user


# ── Register ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await register_user(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    await register_user(client)
    resp = await register_user(client, email="other@example.com")
    assert resp.status_code == 400
    assert "already taken" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await register_user(client)
    resp = await register_user(client, username="otheruser")
    assert resp.status_code == 400
    assert "already taken" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_register_missing_fields(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={"username": "x"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    resp = await register_user(client, email="not-an-email")
    assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await register_user(client)
    resp = await login_user(client)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await register_user(client)
    resp = await login_user(client, password="wrong")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    resp = await login_user(client, username="nobody")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_missing_fields(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={"username": "x"})
    assert resp.status_code == 422


# ── Me ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient):
    headers = await get_auth_headers(client)
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


@pytest.mark.asyncio
async def test_me_no_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_token_no_sub(client: AsyncClient):
    """Valid JWT with missing 'sub' claim — covers auth.py line 41."""
    token = jwt.encode({"exp": 9999999999}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_user_not_found(client: AsyncClient):
    """Valid JWT with sub pointing to non-existent user — covers auth.py line 47."""
    token = jwt.encode({"sub": "nonexistent-user-id", "exp": 9999999999},
                        settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_expired_token(client: AsyncClient):
    """Token that has already expired — covers JWTError branch."""
    token = jwt.encode({"sub": "user-id", "exp": 1}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_tampered_token(client: AsyncClient):
    """Token with corrupted signature."""
    headers = await get_auth_headers(client)
    token = headers["Authorization"].split(" ")[1]
    tampered = token[:-5] + "AAAAA"
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_wrong_scheme(client: AsyncClient):
    """Using Basic auth instead of Bearer."""
    headers = await get_auth_headers(client)
    token = headers["Authorization"].split(" ")[1]
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Basic {token}"})
    assert resp.status_code == 401
