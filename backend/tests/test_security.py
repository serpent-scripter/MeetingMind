import pytest
from core.security import verify_password, get_password_hash, create_access_token
from datetime import timedelta
from core.constants import SecurityConstants

def test_verify_password():
    password = "secretpassword"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)

def test_get_password_hash():
    password = "test"
    hashed = get_password_hash(password)
    assert hashed != password
    assert len(hashed) > 0

def test_create_access_token():
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

    token2 = create_access_token(data, expires_delta=timedelta(minutes=15))
    assert isinstance(token2, str)
