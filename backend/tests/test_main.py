import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db" in data


def test_redirect_to_docs():
    response = client.get("/api/v1/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/api/v1/docs"
