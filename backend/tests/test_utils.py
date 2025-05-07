import pytest
from fastapi import HTTPException
from services.utils import get_object_id
from bson import ObjectId

def test_get_object_id_valid():
    valid_id = str(ObjectId())
    obj_id = get_object_id(valid_id)
    assert isinstance(obj_id, ObjectId)
    assert str(obj_id) == valid_id

def test_get_object_id_invalid():
    with pytest.raises(HTTPException) as excinfo:
        get_object_id("invalid")
    assert excinfo.value.status_code == 400
