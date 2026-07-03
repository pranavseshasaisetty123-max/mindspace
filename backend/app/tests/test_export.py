import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture
async def auth_headers_export():
    """Register and authenticate user for export tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "export_user@example.com", "password": "Password123"}
        )
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "export_user@example.com", "password": "Password123"}
        )
        token = login_res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_export_endpoints_flow(auth_headers_export):
    """Verify that export downloads initiate correctly for both Markdown and ReportLab PDF formats."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a journal entry first
        journal_res = await ac.post(
            "/api/v1/journals",
            headers=auth_headers_export,
            json={
                "title": "Export Test Entry", 
                "content": "This is content for export testing.", 
                "mood": 4, 
                "stress_level": 2, 
                "energy_level": 4, 
                "sleep_hours": 8.0, 
                "tags": ["export", "test"]
            }
        )
        assert journal_res.status_code == 201
        journal_id = journal_res.json()["id"]

        # 1. Export single entry as Markdown (.md)
        res_single_md = await ac.get(
            f"/api/v1/export/journals/{journal_id}?format=md",
            headers=auth_headers_export
        )
        assert res_single_md.status_code == 200
        assert res_single_md.headers["content-type"] == "text/markdown; charset=utf-8"
        assert "Content-Disposition" in res_single_md.headers
        assert "Export Test Entry" in res_single_md.text

        # 2. Export single entry as PDF (.pdf)
        res_single_pdf = await ac.get(
            f"/api/v1/export/journals/{journal_id}?format=pdf",
            headers=auth_headers_export
        )
        assert res_single_pdf.status_code == 200
        assert res_single_pdf.headers["content-type"] == "application/pdf"
        assert len(res_single_pdf.content) > 0 # PDF binary payload

        # 3. Export all history as Markdown (.md)
        res_all_md = await ac.get(
            "/api/v1/export/journals/all?format=md",
            headers=auth_headers_export
        )
        assert res_all_md.status_code == 200
        assert res_all_md.headers["content-type"] == "text/markdown; charset=utf-8"
        assert "Export Test Entry" in res_all_md.text

        # 4. Export all history as PDF (.pdf)
        res_all_pdf = await ac.get(
            "/api/v1/export/journals/all?format=pdf",
            headers=auth_headers_export
        )
        assert res_all_pdf.status_code == 200
        assert res_all_pdf.headers["content-type"] == "application/pdf"
        assert len(res_all_pdf.content) > 0
