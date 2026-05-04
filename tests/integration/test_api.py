"""
Lightweight integration test for the FastAPI app.

The test exercises only endpoints that don't require live AWS - the
health endpoint - so it can run in CI without real Bedrock credentials.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    # Avoid building the singleton vector store on app import
    from src.api.app import create_app
    app = create_app()
    return TestClient(app)


def test_health_endpoint(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "docs" in r.json()


def test_query_validation_error(client):
    # Empty question should be rejected before reaching Bedrock
    r = client.post("/api/v1/query", json={"question": ""})
    assert r.status_code in (400, 422)
