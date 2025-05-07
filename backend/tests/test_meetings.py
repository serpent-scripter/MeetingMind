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
    mock_db_instance.meetings = MagicMock()
    mock_db_instance.transcripts = MagicMock()
    mock_db_instance.summaries = MagicMock()
    mock_db_instance.actionItems = MagicMock()
    mock_db_instance.users = MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_db_instance
    yield mock_db_instance
    app.dependency_overrides.pop(get_db, None)

def test_get_meetings(override_auth, mock_db):
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(
        return_value=[{"_id": "507f1f77bcf86cd799439011", "title": "Meeting 1", "duration": 60, "status": "completed", "recordedAt": "2023-01-01T00:00:00Z"}]
    )
    mock_db.meetings.find.return_value = mock_cursor

    response = client.get("/api/v1/meetings")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_create_meeting(override_auth, mock_db):
    mock_db.meetings.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id="507f1f77bcf86cd799439011")
    )
    mock_db.meetings.find_one = AsyncMock(
        return_value={"_id": "507f1f77bcf86cd799439011", "title": "New Meeting", "duration": 60, "status": "processing", "recordedAt": "2023-01-01T00:00:00Z", "audioFilePath": "dummy.mp3"}
    )
    mock_db.users.update_one = AsyncMock()

    with patch("fastapi.BackgroundTasks.add_task") as mock_add_task, patch("os.makedirs") as mock_makedirs, patch("builtins.open", new_callable=MagicMock), patch("os.path.getsize", return_value=1000):
        response = client.post(
            "/api/v1/meetings",
            data={
                "title": "New Meeting",
                "duration": "60"
            },
            files={"audioFile": ("dummy.mp3", b"dummy content", "audio/mpeg")}
        )

        assert response.status_code == 200
        assert response.json()["title"] == "New Meeting"
        mock_add_task.assert_called()

def test_get_meeting_detail(override_auth, mock_db):
    mock_db.meetings.find_one = AsyncMock(
        return_value={"_id": "507f1f77bcf86cd799439011", "title": "Meeting 1", "duration": 60, "status": "completed", "recordedAt": "2023-01-01T00:00:00Z", "audioFilePath": "dummy.mp3"}
    )

    mock_db.transcripts.find_one = AsyncMock(
        return_value={"_id": "t1", "meetingId": "507f1f77bcf86cd799439011", "content": "Hello", "utterances": []}
    )

    mock_db.summaries.find_one = AsyncMock(
        return_value={"_id": "s1", "meetingId": "507f1f77bcf86cd799439011", "content": "Summary"}
    )

    mock_a_cursor = MagicMock()
    mock_a_cursor.sort.return_value = mock_a_cursor
    mock_a_cursor.to_list = AsyncMock(return_value=[{"_id": "a1", "description": "Action"}])
    mock_db.actionItems.find.return_value = mock_a_cursor

    response = client.get("/api/v1/meetings/507f1f77bcf86cd799439011")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Meeting 1"
    assert data["transcript"]["id"] == "t1"
    assert data["summary"]["id"] == "s1"
    assert len(data["actionItems"]) == 1

def test_delete_meeting(override_auth, mock_db):
    mock_db.meetings.find_one = AsyncMock(
        return_value={
            "_id": "507f1f77bcf86cd799439011",
            "audioFilePath": "dummy.mp3",
            "ownerId": "user123",
        }
    )
    mock_db.transcripts.delete_many = AsyncMock()
    mock_db.summaries.delete_many = AsyncMock()
    mock_db.actionItems.update_many = AsyncMock()
    mock_db.meetings.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove:
        response = client.delete("/api/v1/meetings/507f1f77bcf86cd799439011")
        assert response.status_code == 200
