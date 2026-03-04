"""Test: API Health Endpoints."""
import pytest
from playwright.sync_api import Page, APIRequestContext


@pytest.fixture
def api(playwright):
    """Create API context for direct HTTP testing."""
    ctx = playwright.request.new_context(base_url="http://192.168.86.94:30501")
    yield ctx
    ctx.dispose()


def test_health_endpoint(api: APIRequestContext):
    """Verify /api/health returns healthy status."""
    resp = api.get("/api/health/ready")
    assert resp.status == 200
    data = resp.json()
    assert data["status"] == "ready"


def test_health_live(api: APIRequestContext):
    """Verify /api/health/live returns alive."""
    resp = api.get("/api/health/live")
    assert resp.status == 200
    data = resp.json()
    assert data["status"] == "alive"


def test_health_detailed(api: APIRequestContext):
    """Verify /api/health/detailed returns detailed info."""
    resp = api.get("/api/health/detailed")
    assert resp.status == 200
    data = resp.json()
    assert "status" in data


def test_validate_key_invalid(api: APIRequestContext):
    """Verify validate-key rejects invalid keys."""
    resp = api.post("/api/validate-key", data={
        "api_key": "invalid-key",
        "provider": "openai"
    })
    assert resp.status == 200
    data = resp.json()
    assert data["valid"] is False


def test_generate_mermaid_no_key(api: APIRequestContext):
    """Verify generate-mermaid fails without valid key."""
    resp = api.post("/api/generate-mermaid", data={
        "input": "Create a flowchart",
        "api_key": "invalid",
        "provider": "openai"
    })
    # Should return error (either 400, 401, or 500)
    assert resp.status >= 400 or (resp.status == 200 and not resp.json().get("success", True))


def test_static_css_served(api: APIRequestContext):
    """Verify static CSS is served correctly."""
    resp = api.get("/static/styles.css")
    assert resp.status == 200
    assert "text/css" in resp.headers.get("content-type", "")


def test_static_js_served(api: APIRequestContext):
    """Verify static JS is served correctly."""
    resp = api.get("/static/app.js")
    assert resp.status == 200
    assert "javascript" in resp.headers.get("content-type", "")
