import pytest
import json
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture
async def auth_headers_user1():
    """Register and authenticate user1, yielding their bearer headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "ref1@example.com", "password": "Password123"}
        )
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "ref1@example.com", "password": "Password123"}
        )
        token = login_res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def auth_headers_user2():
    """Register and authenticate user2, yielding their bearer headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "ref2@example.com", "password": "Password123"}
        )
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "ref2@example.com", "password": "Password123"}
        )
        token = login_res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_generate_reflection_success(auth_headers_user1):
    """Verify triggering reflection generation works, returning structured Pydantic schema."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create Journal Entry
        journal_res = await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={"title": "Productive Day", "content": "I built custom components and ran tests.", "mood": 4, "stress_level": 2, "energy_level": 4, "sleep_hours": 8.0, "tags": []}
        )
        journal_id = journal_res.json()["id"]

        # Mock Gemini call
        mock_response = {
            "summary": "You had a productive day working on components.",
            "detected_patterns": ["Productivity", "Mindfulness"],
            "reflection_question": "What will you build tomorrow?",
            "model_used": "mock-gemini-test"
        }

        with patch("app.services.gemini.generate_reflection_from_gemini", return_value=mock_response):
            response = await ac.post(
                f"/api/v1/journals/{journal_id}/generate-reflection",
                headers=auth_headers_user1
            )
            
        assert response.status_code == 200
        data = response.json()
        assert data["journal_id"] == journal_id
        assert data["summary"] == "You had a productive day working on components."
        assert data["detected_patterns"] == ["Productivity", "Mindfulness"]
        assert data["reflection_question"] == "What will you build tomorrow?"
        assert data["model_used"] == "mock-gemini-test"

@pytest.mark.asyncio
async def test_get_reflection_cache_reuse(auth_headers_user1):
    """Verify getting cached reflections returns same record if entry is unchanged."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create Journal
        journal_res = await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={"title": "Same Entry", "content": "No updates expected.", "mood": 3, "stress_level": 3, "energy_level": 3, "sleep_hours": 7.0, "tags": []}
        )
        journal_id = journal_res.json()["id"]

        # Mock Gemini
        mock_response = {
            "summary": "Original summary.",
            "detected_patterns": ["Routine"],
            "reflection_question": "Is this a habit?",
            "model_used": "mock-gemini-test"
        }

        with patch("app.services.gemini.generate_reflection_from_gemini", return_value=mock_response):
            # Generate first
            gen_res = await ac.post(
                f"/api/v1/journals/{journal_id}/generate-reflection",
                headers=auth_headers_user1
            )
            first_reflection_id = gen_res.json()["id"]

            # Fetch via GET
            get_res = await ac.get(
                f"/api/v1/journals/{journal_id}/reflection",
                headers=auth_headers_user1
            )
            assert get_res.status_code == 200
            assert get_res.json()["id"] == first_reflection_id

@pytest.mark.asyncio
async def test_reflection_cache_invalidation_on_update(auth_headers_user1):
    """Verify updating a journal entry invalidates cached reflection."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create Journal
        journal_res = await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={"title": "Initial Title", "content": "Old Content.", "mood": 3, "stress_level": 3, "energy_level": 3, "sleep_hours": 7.0, "tags": []}
        )
        journal_id = journal_res.json()["id"]

        # Mock Gemini response
        mock_response = {
            "summary": "Old Summary.",
            "detected_patterns": ["Old"],
            "reflection_question": "Old Question?",
            "model_used": "mock-gemini-test"
        }

        with patch("app.services.gemini.generate_reflection_from_gemini", return_value=mock_response):
            await ac.post(
                f"/api/v1/journals/{journal_id}/generate-reflection",
                headers=auth_headers_user1
            )

        # Update Journal content (invalidates cache!)
        import asyncio
        await asyncio.sleep(1.1)
        await ac.put(
            f"/api/v1/journals/{journal_id}",
            headers=auth_headers_user1,
            json={"title": "Updated Title", "content": "Brand New Content."}
        )

        # Try to GET reflection (should return 404 because cache is now stale!)
        get_res = await ac.get(
            f"/api/v1/journals/{journal_id}/reflection",
            headers=auth_headers_user1
        )
        assert get_res.status_code == 404

@pytest.mark.asyncio
async def test_crisis_safety_bypass(auth_headers_user1):
    """Verify crisis keywords bypass LLM generation, returning crisis hotline details immediately."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create Journal with self-harm crisis language
        journal_res = await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={"title": "Hard Night", "content": "I am feeling so overwhelmed and want to self-harm.", "mood": 1, "stress_level": 5, "energy_level": 1, "sleep_hours": 4.0, "tags": []}
        )
        journal_id = journal_res.json()["id"]

        # Request reflection without mocking (Gemini should be bypassed anyway)
        response = await ac.post(
            f"/api/v1/journals/{journal_id}/generate-reflection",
            headers=auth_headers_user1
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["model_used"] == "safety_filter"
        assert "741741" in data["reflection_question"]
        assert "safe" in data["summary"]

@pytest.mark.asyncio
async def test_reflection_ownership_protection(auth_headers_user1, auth_headers_user2):
    """Verify User 2 cannot fetch or trigger reflections on User 1's journal entries."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # User 1 creates journal
        journal_res = await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={"title": "User1 Log", "content": "Secret text.", "mood": 3, "stress_level": 3, "energy_level": 3, "sleep_hours": 7.0, "tags": []}
        )
        journal_id = journal_res.json()["id"]

        # User 2 tries to GET reflection
        get_res = await ac.get(
            f"/api/v1/journals/{journal_id}/reflection",
            headers=auth_headers_user2
        )
        assert get_res.status_code == 403

        # User 2 tries to POST generate-reflection
        post_res = await ac.post(
            f"/api/v1/journals/{journal_id}/generate-reflection",
            headers=auth_headers_user2
        )
        assert post_res.status_code == 403

async def mock_sleep(seconds):
    pass

@pytest.mark.asyncio
async def test_reflection_retry_and_fallback_to_stale_cache(auth_headers_user1):
    """Verify that if Gemini fails all retries, it gracefully falls back to the stale cache and flags it outdated."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create entry
        journal_res = await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={"title": "Stale Cache Fallback", "content": "Initial thoughts.", "mood": 3, "stress_level": 3, "energy_level": 3, "sleep_hours": 7.0, "tags": []}
        )
        journal_id = journal_res.json()["id"]

        # 2. Generate a valid cached reflection
        mock_response = {
            "summary": "Original reflection.",
            "detected_patterns": ["Original"],
            "reflection_question": "Original Question?",
            "model_used": "mock-gemini-test"
        }
        with patch("app.services.gemini.generate_reflection_from_gemini", return_value=mock_response):
            await ac.post(
                f"/api/v1/journals/{journal_id}/generate-reflection",
                headers=auth_headers_user1
            )

        # 3. Sleep and update journal to make cache stale
        import asyncio
        await asyncio.sleep(1.1)
        await ac.put(
            f"/api/v1/journals/{journal_id}",
            headers=auth_headers_user1,
            json={"title": "Stale Cache Fallback", "content": "Updated thoughts."}
        )

        # 4. Request reflection, mocking Gemini API to throw exception
        with patch("app.services.gemini.generate_reflection_from_gemini", side_effect=Exception("API limit hit")):
            with patch("asyncio.sleep", side_effect=mock_sleep):
                response = await ac.post(
                    f"/api/v1/journals/{journal_id}/generate-reflection",
                    headers=auth_headers_user1
                )

        assert response.status_code == 200
        data = response.json()
        assert data["is_outdated"] is True
        assert data["summary"] == "Original reflection."
        assert data["model_used"] == "mock-gemini-test"

@pytest.mark.asyncio
async def test_reflection_retry_and_fallback_to_local_fallback(auth_headers_user1):
    """Verify that if Gemini fails all retries and no cache exists, it generates a local fallback reflection."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create entry (no cached reflection exists yet)
        journal_res = await ac.post(
            "/api/v1/journals",
            headers=auth_headers_user1,
            json={"title": "Local Fallback Test", "content": "Today I had a happy day and worked hard.", "mood": 4, "stress_level": 2, "energy_level": 4, "sleep_hours": 8.0, "tags": []}
        )
        journal_id = journal_res.json()["id"]

        # 2. Request reflection, mocking Gemini to fail
        with patch("app.services.gemini.generate_reflection_from_gemini", side_effect=Exception("Gemini high load 503")):
            with patch("asyncio.sleep", side_effect=mock_sleep):
                response = await ac.post(
                    f"/api/v1/journals/{journal_id}/generate-reflection",
                    headers=auth_headers_user1
                )

        assert response.status_code == 200
        data = response.json()
        assert data["is_outdated"] is False
        assert data["model_used"] == "Local Fallback"
        assert "temporarily busy" in data["summary"]
        assert "Happy" in data["detected_patterns"] or "Work" in data["detected_patterns"]
        assert len(data["reflection_question"]) > 0

