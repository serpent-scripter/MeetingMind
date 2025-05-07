from bson import ObjectId
from fastapi import HTTPException

from core.constants import ErrorMessages


def get_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail=ErrorMessages.INVALID_ID_FORMAT)
