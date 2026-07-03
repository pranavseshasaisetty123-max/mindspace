import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.utils.security import auth_rate_limiter

@pytest.mark.asyncio
async def test_diagnostics_health_check():
    """Verify health diagnostics endpoint returns 200 and loads checklist parameters."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "uptime_seconds" in data
        assert "version" in data
        assert "gemini_configured" in data

@pytest.mark.asyncio
async def test_diagnostics_readiness_check():
    """Verify readiness check responds with 200 ready state."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/ready")
        assert res.status_code == 200
        assert res.json() == {"status": "ready"}

@pytest.mark.asyncio
async def test_security_headers_injection():
    """Verify security headers are successfully injected on responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/health")
        assert "X-Request-ID" in res.headers
        assert res.headers["X-Frame-Options"] == "DENY"
        assert res.headers["X-Content-Type-Options"] == "nosniff"
        assert res.headers["X-XSS-Protection"] == "1; mode=block"
        assert res.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

@pytest.mark.asyncio
async def test_auth_sliding_window_rate_limiting():
    """Verify auth endpoints trigger HTTP 429 on excessive requests."""
    auth_rate_limiter.enabled = True
    auth_rate_limiter.requests.clear()
    
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Issue 5 requests (the window limit boundary)
            for _ in range(5):
                res = await ac.post(
                    "/api/v1/auth/login",
                    json={"email": "rate@example.com", "password": "Pass"}
                )
                # Should not be rate-limited yet (returns 401/422 depending on checks)
                assert res.status_code != 429
                
            # The 6th request must trigger rate-limiting HTTP 429
            res_limit = await ac.post(
                "/api/v1/auth/login",
                json={"email": "rate@example.com", "password": "Pass"}
            )
            assert res_limit.status_code == 429
            assert "too many" in res_limit.json()["detail"].lower()
    finally:
        # Reset and disable limiter state to release IP block for other tests
        auth_rate_limiter.enabled = False
        auth_rate_limiter.requests.clear()

@pytest.mark.asyncio
async def test_route_not_found_structured_json():
    """Verify 404 errors return a standardized JSON error format."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/invalid-route-endpoints")
        assert res.status_code == 404
        data = res.json()
        assert data["status_code"] == 404
        assert "detail" in data
        assert "request_id" in data

@pytest.mark.asyncio
async def test_unauthorized_token_structured_json():
    """Verify 401 errors return a standardized JSON error format."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/journals", headers={"Authorization": "Bearer invalidtoken"})
        assert res.status_code == 401
        data = res.json()
        assert data["status_code"] == 401
        assert "detail" in data
        assert "request_id" in data

@pytest.mark.asyncio
async def test_validation_failure_structured_json():
    """Verify 422 errors return a standardized JSON error format."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/auth/register",
            json={"email": "invalidemail"} # Missing password
        )
        assert res.status_code == 422
        data = res.json()
        assert data["status_code"] == 422
        assert "errors" in data
        assert "request_id" in data
