import pytest
from fastapi.testclient import TestClient
from main import app
from api.routers.auth import get_current_user
from unittest.mock import patch, MagicMock, AsyncMock

client = TestClient(app)


@pytest.fixture
def mock_db():
    mock_db_instance = MagicMock()
    mock_db_instance.users = MagicMock()
    mock_db_instance.meetings = MagicMock()
    mock_db_instance.transcripts = MagicMock()
    mock_db_instance.summaries = MagicMock()
    mock_db_instance.actionItems = MagicMock()

    from db.database import get_db

    app.dependency_overrides[get_db] = lambda: mock_db_instance
    yield mock_db_instance
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def override_auth():
    async def mock_user():
        return {"_id": "test_id", "email": "test@example.com", "name": "Test User"}

    app.dependency_overrides[get_current_user] = mock_user
    yield
    app.dependency_overrides = {}


def test_update_user_me(mock_db, override_auth):
    mock_db.users.update_one = AsyncMock()

    response = client.patch("/api/v1/users/me", json={"name": "New Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    mock_db.users.update_one.assert_called_once()

    response2 = client.patch("/api/v1/users/me", json={"password": "newpassword"})
    assert response2.status_code == 200


def test_delete_user_me(mock_db, override_auth):
    # Setup mock to return a list of meetings
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(
        return_value=[{"_id": "meeting1", "audioFilePath": "/path/to/audio.mp3"}]
    )
    mock_db.meetings.find.return_value = mock_cursor

    mock_db.transcripts.delete_many = AsyncMock()
    mock_db.summaries.delete_many = AsyncMock()
    mock_db.actionItems.delete_many = AsyncMock()
    mock_db.meetings.delete_many = AsyncMock()
    mock_db.users.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))

    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove:
        response = client.delete("/api/v1/users/me")
        assert response.status_code == 200
        assert response.json() == {"message": "Account deleted"}
        mock_remove.assert_called_once()
        mock_db.users.delete_one.assert_called_once()


def test_delete_user_not_found(mock_db, override_auth):
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_db.meetings.find.return_value = mock_cursor

    mock_db.transcripts.delete_many = AsyncMock()
    mock_db.summaries.delete_many = AsyncMock()
    mock_db.actionItems.delete_many = AsyncMock()
    mock_db.meetings.delete_many = AsyncMock()
    mock_db.users.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))

    response = client.delete("/api/v1/users/me")
    assert response.status_code == 404
