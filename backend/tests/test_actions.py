import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, patch, MagicMock
from api.routers.auth import get_current_user
from db.database import get_db

client = TestClient(app)


@pytest.fixture
def override_auth():
    async def mock_user():
        return {"_id": "user123", "email": "test@example.com", "name": "Test User"}

    app.dependency_overrides[get_current_user] = mock_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def mock_db():
    mock_db_instance = MagicMock()
    mock_db_instance.actionItems = MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_db_instance
    yield mock_db_instance
    app.dependency_overrides.pop(get_db, None)


def test_get_action_items(override_auth, mock_db):
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(
        return_value=[
            {"_id": "507f1f77bcf86cd799439011", "text": "Action 1", "status": "pending"}
        ]
    )
    mock_db.actionItems.find.return_value = mock_cursor

    response = client.get("/api/v1/actions")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_update_action_item(override_auth, mock_db):
    mock_db.actionItems.find_one = AsyncMock(
        side_effect=[
            {"_id": "507f1f77bcf86cd799439011", "ownerId": "user123"},
            {"_id": "507f1f77bcf86cd799439011", "status": "completed"},
        ]
    )
    mock_db.actionItems.update_one = AsyncMock()

    response = client.patch(
        "/api/v1/actions/507f1f77bcf86cd799439011", json={"status": "completed"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    mock_db.actionItems.update_one.assert_called_once()


def test_update_action_item_not_found(override_auth, mock_db):
    mock_db.actionItems.find_one = AsyncMock(return_value=None)
    response = client.patch(
        "/api/v1/actions/507f1f77bcf86cd799439011", json={"status": "completed"}
    )
    assert response.status_code == 404


def test_delete_action_item(override_auth, mock_db):
    mock_db.actionItems.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    response = client.delete("/api/v1/actions/507f1f77bcf86cd799439011")
    assert response.status_code == 200
    assert response.json()["message"] == "Action item archived"
