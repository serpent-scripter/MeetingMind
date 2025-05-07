import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from services.tasks import process_meeting_audio

@pytest.mark.asyncio
@patch("services.tasks._transcribe_audio")
@patch("services.tasks._generate_summary")
@patch("services.tasks._extract_action_items")
async def test_process_meeting_audio(mock_actions, mock_summary, mock_transcribe):
    mock_transcribe.return_value = ("Hello", [{"text": "Hello", "start": 0, "end": 1}], True)
    mock_summary.return_value = ("Summary text", ["Point 1"], True)
    mock_actions.return_value = ("Action 1", "John", True)

    with patch("services.tasks.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.meetings.find_one = AsyncMock(
            return_value={"_id": "m1", "audioFilePath": "dummy.mp3", "ownerId": "u1"}
        )
        mock_db.meetings.update_one = AsyncMock()
        mock_db.transcripts.insert_one = AsyncMock()
        mock_db.summaries.insert_one = AsyncMock()
        mock_db.actionItems.insert_one = AsyncMock()

        await process_meeting_audio("507f1f77bcf86cd799439011")
        mock_db.meetings.update_one.assert_called()
