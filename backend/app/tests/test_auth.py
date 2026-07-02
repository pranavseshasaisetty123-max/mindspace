import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_register_user_success():
    """Verify new user registration works and returns sanitized profile."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"}
        )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password_hash" not in data  # Assert that hashed password is never returned

@pytest.mark.asyncio
async def test_register_user_duplicate():
    """Verify registration checks duplicate constraints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First creation
        response = await ac.post(
            "/api/v1/auth/register",
            json={"email": "dup@example.com", "password": "password123"}
        )
        assert response.status_code == 201
        
        # Duplicate registration attempt
        response = await ac.post(
            "/api/v1/auth/register",
            json={"email": "dup@example.com", "password": "password123"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_register_weak_password_no_digit():
    """Verify registration fails if password lacks at least one digit."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/register",
            json={"email": "weak1@example.com", "password": "passwordonly"}
        )
    assert response.status_code == 422
    assert "Password must contain at least one digit" in response.json()["detail"]

@pytest.mark.asyncio
async def test_register_weak_password_no_letter():
    """Verify registration fails if password lacks at least one letter."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/register",
            json={"email": "weak2@example.com", "password": "123456789"}
        )
    assert response.status_code == 422
    assert "Password must contain at least one letter" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_success():
    """Verify login works for registered accounts and returns signed JWT."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register Account
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "login@example.com", "password": "password123"}
        )
        
        # Perform authentication
        response = await ac.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_failure():
    """Verify authentication fails for bad password credentials."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Authenticate invalid account
        response = await ac.post(
            "/api/v1/auth/login",
            json={"email": "noexist@example.com", "password": "password123"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_profile_unauthorized():
    """Verify profile route blocks missing authorization headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/profile")
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_profile_authorized():
    """Verify profile retrieves authentic profile data when passed valid Bearer JWT."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register and Authenticate
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "profile@example.com", "password": "password123"}
        )
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "profile@example.com", "password": "password123"}
        )
        token = login_res.json()["access_token"]
        
        # Load protected profile route
        response = await ac.get(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "profile@example.com"
