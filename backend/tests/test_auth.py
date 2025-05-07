import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock, AsyncMock
from core.security import get_password_hash, create_access_token

client = TestClient(app)

@pytest.fixture
def mock_db():
    with patch("api.routers.auth.get_db") as mock_get_db:
        mock_db_instance = MagicMock()
        mock_db_instance.users = MagicMock()
        mock_get_db.return_value = mock_db_instance
        yield mock_db_instance

def test_signup_success(mock_db):
    mock_db.users.find_one = AsyncMock(return_value=None)
    mock_db.users.insert_one = AsyncMock()

    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "password123", "name": "Test User"}
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"

def test_signup_existing_email(mock_db):
    mock_db.users.find_one = AsyncMock(return_value={"email": "test@example.com"})

    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "password123", "name": "Test User"}
    )
    assert response.status_code == 400

def test_login_success(mock_db):
    hashed_password = get_password_hash("password123")
    mock_db.users.find_one = AsyncMock(return_value={"email": "test@example.com", "passwordHash": hashed_password})

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure(mock_db):
    hashed_password = get_password_hash("password123")
    mock_db.users.find_one = AsyncMock(return_value={"email": "test@example.com", "passwordHash": hashed_password})

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_login_user_not_found(mock_db):
    mock_db.users.find_one = AsyncMock(return_value=None)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "notfound@example.com", "password": "password123"}
    )
    assert response.status_code == 401

def test_logout():
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}

def test_get_me_success(mock_db):
    access_token = create_access_token(data={"sub": "test@example.com"})
    mock_db.users.find_one = AsyncMock(return_value={"_id": "someid", "email": "test@example.com", "name": "Test User", "storageUsed": 0})

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_get_me_invalid_token(mock_db):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401
