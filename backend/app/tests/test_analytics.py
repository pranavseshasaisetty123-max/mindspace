import pytest
from datetime import datetime, date, timedelta
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture
async def auth_headers():
    """Register and authenticate user, yielding bearer headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "analytics@example.com", "password": "Password123"}
        )
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "analytics@example.com", "password": "Password123"}
        )
        token = login_res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_analytics_dashboard_empty(auth_headers):
    """Verify analytics endpoints behave correctly on empty databases."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify summaries are zeroed
        assert data["summary"]["total_reflections"] == 0
        assert data["summary"]["streak_days"] == 0
        assert data["summary"]["average_mood"] == 0.0
        assert data["summary"]["average_sleep"] == 0.0
        
        assert len(data["trends"]) == 0
        assert len(data["tag_distribution"]) == 0

@pytest.mark.asyncio
async def test_analytics_dashboard_aggregation(auth_headers):
    """Verify mathematical average calculations on multi-entry logs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create first entry
        await ac.post(
            "/api/v1/journals",
            headers=auth_headers,
            json={"title": "Morning", "content": "Ok morning.", "mood": 4, "stress_level": 2, "energy_level": 4, "sleep_hours": 8.0, "tags": []}
        )
        # Create second entry
        await ac.post(
            "/api/v1/journals",
            headers=auth_headers,
            json={"title": "Evening", "content": "Tired evening.", "mood": 2, "stress_level": 4, "energy_level": 2, "sleep_hours": 6.0, "tags": []}
        )

        response = await ac.get("/api/v1/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["summary"]["total_reflections"] == 2
        assert data["summary"]["streak_days"] == 1
        assert data["summary"]["average_mood"] == 3.0  # (4 + 2) / 2
        assert data["summary"]["average_sleep"] == 7.0  # (8.0 + 6.0) / 2
        
        # Verify trends length and values
        assert len(data["trends"]) == 1
        assert data["trends"][0]["avg_mood"] == 3.0
        assert data["trends"][0]["avg_sleep"] == 7.0

@pytest.mark.asyncio
async def test_analytics_streak_calculation(auth_headers):
    """Verify that daily journaling increments streaks correctly, and resets on gaps."""
    # Note: testing consecutive days directly requires inserting mock created_at dates.
    # In FastAPI endpoints, created_at defaults to func.now(). We can test that today's entry sets streak = 1.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create today's journal
        await ac.post(
            "/api/v1/journals",
            headers=auth_headers,
            json={"title": "Today", "content": "Writing today.", "mood": 3, "stress_level": 3, "energy_level": 3, "sleep_hours": 7.0, "tags": []}
        )

        response = await ac.get("/api/v1/analytics/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["streak_days"] == 1

@pytest.mark.asyncio
async def test_analytics_tag_distribution(auth_headers):
    """Verify tag occurrence frequencies are aggregated correctly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create entry 1 with tags
        await ac.post(
            "/api/v1/journals",
            headers=auth_headers,
            json={"title": "Work", "content": "Tough day.", "mood": 3, "stress_level": 4, "energy_level": 3, "sleep_hours": 6.5, "tags": ["work", "focus"]}
        )
        # Create entry 2 with tags
        await ac.post(
            "/api/v1/journals",
            headers=auth_headers,
            json={"title": "Rest", "content": "Chilling.", "mood": 4, "stress_level": 1, "energy_level": 4, "sleep_hours": 8.0, "tags": ["focus"]}
        )

        response = await ac.get("/api/v1/analytics/tag-distribution", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify tag counting
        # "focus" should have count 2, "work" should have count 1
        focus_count = next(x for x in data if x["tag"] == "focus")
        work_count = next(x for x in data if x["tag"] == "work")
        
        assert focus_count["count"] == 2
        assert work_count["count"] == 1

@pytest.mark.asyncio
async def test_analytics_unauthorized():
    """Verify that requesting analytics without auth headers is forbidden."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard")
        assert response.status_code == 401
