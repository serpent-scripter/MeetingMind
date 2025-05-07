import os

from fastapi import APIRouter, Depends, HTTPException, status

from db.database import get_db
from api.routers.auth import get_current_user
from schemas.models import UserResponse, UserUpdate
from core.security import get_password_hash
from core.constants import ErrorMessages, PaginationLimits

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserResponse)
async def update_user_me(
    item: UserUpdate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    update_data = {}
    if item.name is not None:
        update_data["name"] = item.name
    if item.password is not None:
        update_data["passwordHash"] = get_password_hash(item.password)

    if update_data:
        await db.users.update_one({"_id": current_user["_id"]}, {"$set": update_data})

    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        name=update_data.get("name", current_user.get("name", "")),
        storageUsed=current_user.get("storageUsed", 0),
    )


@router.delete("/me")
async def delete_user_me(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["_id"]
    meetings = await db.meetings.find({"ownerId": user_id}).to_list(
        length=PaginationLimits.MAX_SEARCH_LIMIT
    )
    meeting_ids = [meeting["_id"] for meeting in meetings]

    for meeting in meetings:
        audio_path = meeting.get("audioFilePath", "")
        if not audio_path:
            continue

        file_path = os.path.join(
            os.path.dirname(__file__), "..", audio_path.lstrip("/")
        )
        file_path = os.path.abspath(file_path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                # If file cleanup fails, continue deleting DB data so the account is still removed.
                pass

    if meeting_ids:
        await db.transcripts.delete_many({"meetingId": {"$in": meeting_ids}})
        await db.summaries.delete_many({"meetingId": {"$in": meeting_ids}})
        await db.actionItems.delete_many({"meetingId": {"$in": meeting_ids}})
        await db.meetings.delete_many({"_id": {"$in": meeting_ids}})

    await db.actionItems.delete_many({"ownerId": user_id})

    # Actually delete user
    res = await db.users.delete_one({"_id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail=ErrorMessages.USER_NOT_FOUND)

    return {"message": "Account deleted"}
