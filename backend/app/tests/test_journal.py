import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture
async def auth_headers_user1():
    """Register and authenticate user1, yielding their bearer token headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "user1@example.com", "password": "Password123"}
        )
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "user1@example.com", "password": "Password123"}
        )
        token = login_res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def auth_headers_user2():
    """Register and authenticate user2, yielding their bearer token headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "user2@example.com", "password": "Password123"}
        )
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "user2@example.com", "password": "Password123"}
        )
        token = login_res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_create_journal_success(auth_headers_user1):
    """Verify creating a journal entry with metrics and tags works."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={
                "title": "Study Session",
                "content": "Worked on database schemas and models.",
                "mood": 4,
                "stress_level": 2,
                "energy_level": 4,
                "sleep_hours": 7.5,
                "tags": ["college", "db"]
            }
        )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Study Session"
    assert data["mood"] == 4
    assert len(data["tags"]) == 2
    assert {t["name"] for t in data["tags"]} == {"college", "db"}

@pytest.mark.asyncio
async def test_create_journal_validation_error(auth_headers_user1):
    """Verify journal creation blocks metrics out of 1-5 range."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={
                "title": "Invalid entry",
                "content": "Negative mood rating.",
                "mood": 0,  # Invalid, must be ge=1
                "stress_level": 6,  # Invalid, must be le=5
                "energy_level": 3,
                "sleep_hours": -1.0,  # Invalid, must be ge=0.0
                "tags": []
            }
        )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_journals_pagination_and_filters(auth_headers_user1):
    """Verify list journals queries filter by mood, tag, search string, and apply pagination."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create 3 journals
        await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={"title": "Happy Day", "content": "Went for a run.", "mood": 5, "stress_level": 1, "energy_level": 5, "sleep_hours": 8.0, "tags": ["sports"]}
        )
        await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={"title": "Sad Day", "content": "Tired. Hard workout.", "mood": 2, "stress_level": 3, "energy_level": 2, "sleep_hours": 5.5, "tags": ["sports", "tired"]}
        )
        await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={"title": "Exam Prep", "content": "Studying all night.", "mood": 3, "stress_level": 4, "energy_level": 3, "sleep_hours": 6.0, "tags": ["college"]}
        )

        # 1. Test Tag filter
        response = await ac.get("/api/v1/journals?tag=sports", headers=auth_headers_user1)
        assert response.status_code == 200
        assert len(response.json()) == 2

        # 2. Test Mood filter
        response = await ac.get("/api/v1/journals?mood=5", headers=auth_headers_user1)
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Happy Day"

        # 3. Test Search filter
        response = await ac.get("/api/v1/journals?search=workout", headers=auth_headers_user1)
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Sad Day"

        # 4. Test Pagination
        response = await ac.get("/api/v1/journals?limit=2", headers=auth_headers_user1)
        assert response.status_code == 200
        assert len(response.json()) == 2

@pytest.mark.asyncio
async def test_journal_ownership_protection(auth_headers_user1, auth_headers_user2):
    """Verify user2 cannot read or manipulate user1's journal entries."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # User 1 creates journal
        create_res = await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={"title": "Secret log", "content": "User1 content", "mood": 3, "stress_level": 2, "energy_level": 3, "sleep_hours": 7.0, "tags": []}
        )
        entry_id = create_res.json()["id"]

        # User 2 tries to GET User 1's journal
        get_res = await ac.get(f"/api/v1/journals/{entry_id}", headers=auth_headers_user2)
        assert get_res.status_code == 403

        # User 2 tries to UPDATE User 1's journal
        put_res = await ac.put(
            f"/api/v1/journals/{entry_id}",
            headers=auth_headers_user2,
            json={"title": "Hacked Title"}
        )
        assert put_res.status_code == 403

        # User 2 tries to DELETE User 1's journal
        del_res = await ac.delete(f"/api/v1/journals/{entry_id}", headers=auth_headers_user2)
        assert del_res.status_code == 403

@pytest.mark.asyncio
async def test_journal_soft_delete(auth_headers_user1):
    """Verify deleting a journal flags it as soft-deleted and hides it from lists and detail fetches."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create journal
        create_res = await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={"title": "To delete", "content": "Self-destruct logs.", "mood": 3, "stress_level": 3, "energy_level": 3, "sleep_hours": 6.5, "tags": ["trash"]}
        )
        entry_id = create_res.json()["id"]

        # Delete journal (soft delete)
        del_res = await ac.delete(f"/api/v1/journals/{entry_id}", headers=auth_headers_user1)
        assert del_res.status_code == 200
        assert del_res.json()["deleted_at"] is not None

        # Try to GET detail (should return 404 because soft deleted)
        get_res = await ac.get(f"/api/v1/journals/{entry_id}", headers=auth_headers_user1)
        assert get_res.status_code == 404

        # Try to list journals (should be empty because filtered out)
        list_res = await ac.get("/api/v1/journals", headers=auth_headers_user1)
        assert list_res.status_code == 200
        assert len(list_res.json()) == 0
