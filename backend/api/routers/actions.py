from fastapi import APIRouter, Depends, HTTPException
from typing import List

from db.database import get_db
from api.routers.auth import get_current_user
from schemas.models import ActionItemResponse, ActionItemCreate, ActionItemUpdate

from services.utils import get_object_id
from core.constants import ErrorMessages, PaginationLimits, ActionItemStatus

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("", response_model=List[ActionItemResponse])
async def list_actions(
    db=Depends(get_db), current_user: dict = Depends(get_current_user)
):
    cursor = db.actionItems.find(
        {"ownerId": current_user["_id"], "status": {"$ne": ActionItemStatus.ARCHIVED}}
    )
    docs = await cursor.to_list(length=PaginationLimits.DEFAULT_LIST_LIMIT)

    result = []
    for ai in docs:
        result.append(
            ActionItemResponse(
                id=str(ai["_id"]),
                description=ai.get("description", ""),
                status=ai.get("status", ActionItemStatus.PENDING),
                dueDate=ai.get("dueDate"),
                meetingId=str(ai.get("meetingId", "")) if ai.get("meetingId") else None,
                assignee=ai.get("assignee"),
            )
        )
    return result


@router.post("", response_model=ActionItemResponse)
async def create_action_item(
    item: ActionItemCreate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    meeting_obj_id = get_object_id(item.meetingId)

    # Verify meeting exists and belongs to user
    meeting = await db.meetings.find_one(
        {
            "_id": meeting_obj_id,
            "ownerId": current_user["_id"],
            "isArchived": {"$ne": True},
        }
    )
    if not meeting:
        raise HTTPException(status_code=404, detail=ErrorMessages.MEETING_NOT_FOUND)

    new_doc = {
        "meetingId": meeting_obj_id,
        "ownerId": current_user["_id"],
        "description": item.description,
        "status": ActionItemStatus.PENDING,
        "dueDate": None,
        "source": "manual",
        "assignee": item.assignee,
    }

    res = await db.actionItems.insert_one(new_doc)

    return ActionItemResponse(
        id=str(res.inserted_id),
        description=item.description,
        status=ActionItemStatus.PENDING,
        dueDate=None,
        meetingId=item.meetingId,
        assignee=item.assignee,
    )


@router.patch("/{id}", response_model=ActionItemResponse)
async def update_action_item(
    id: str,
    item: ActionItemUpdate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    obj_id = get_object_id(id)

    ai = await db.actionItems.find_one({"_id": obj_id, "ownerId": current_user["_id"]})
    if not ai:
        raise HTTPException(status_code=404, detail=ErrorMessages.ACTION_ITEM_NOT_FOUND)

    update_data = {}
    if item.description is not None:
        update_data["description"] = item.description
    if item.status is not None:
        update_data["status"] = item.status
    if item.dueDate is not None:
        update_data["dueDate"] = item.dueDate
    if item.assignee is not None:
        update_data["assignee"] = item.assignee

    if update_data:
        await db.actionItems.update_one({"_id": obj_id}, {"$set": update_data})

    # Fetch updated
    ai = await db.actionItems.find_one({"_id": obj_id})
    return ActionItemResponse(
        id=str(ai["_id"]),
        description=ai.get("description", ""),
        status=ai.get("status", ActionItemStatus.PENDING),
        dueDate=ai.get("dueDate"),
        meetingId=str(ai.get("meetingId", "")) if ai.get("meetingId") else None,
        assignee=ai.get("assignee"),
    )


@router.delete("/{id}")
async def archive_action_item(
    id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    obj_id = get_object_id(id)

    res = await db.actionItems.update_one(
        {"_id": obj_id, "ownerId": current_user["_id"]},
        {"$set": {"status": ActionItemStatus.ARCHIVED}},
    )

    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail=ErrorMessages.ACTION_ITEM_NOT_FOUND)

    return {"message": "Action item archived"}
