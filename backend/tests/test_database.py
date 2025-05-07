import pytest
from db.database import db_state, get_db
from fastapi import HTTPException
from unittest.mock import MagicMock, patch


def test_get_db_success():
    db_state.client = MagicMock()
    db_state.client.get_default_database.return_value = "mock_db"
    assert get_db() == "mock_db"


def test_get_db_failure():
    db_state.client = None
    with pytest.raises(HTTPException):
        get_db()
