import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture
async def auth_headers_settings():
    """Register and authenticate user for settings tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "settings_user@example.com", "password": "Password123"}
        )
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "settings_user@example.com", "password": "Password123"}
        )
        token = login_res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_get_settings_seeds_defaults(auth_headers_settings):
    """Verify that requesting settings seeds default preferences configurations on miss."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/settings", headers=auth_headers_settings)
        assert response.status_code == 200
        data = response.json()
        assert data["reminder_enabled"] is False
        assert data["reminder_time"] == "21:00"
        assert data["timezone"] == "UTC"
        assert data["theme"] == "dark"

@pytest.mark.asyncio
async def test_update_settings_success(auth_headers_settings):
    """Verify modifying theme, timezone, and reminder preferences saves changes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.put(
            "/api/v1/settings",
            headers=auth_headers_settings,
            json={"reminder_enabled": True, "reminder_time": "08:30", "theme": "light"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["reminder_enabled"] is True
        assert data["reminder_time"] == "08:30"
        assert data["theme"] == "light"
        assert data["timezone"] == "UTC"  # Verify timezone remains unchanged

@pytest.mark.asyncio
async def test_update_settings_validation_error(auth_headers_settings):
    """Verify invalid reminder times trigger pydantic 422 HTTP validation warnings."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Invalid hour (25:00)
        res_hour = await ac.put(
            "/api/v1/settings",
            headers=auth_headers_settings,
            json={"reminder_time": "25:00"}
        )
        assert res_hour.status_code == 422

        # 2. Invalid minutes (08:61)
        res_min = await ac.put(
            "/api/v1/settings",
            headers=auth_headers_settings,
            json={"reminder_time": "08:61"}
        )
        assert res_min.status_code == 422
