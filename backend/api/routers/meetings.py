from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    Query,
)
from fastapi.responses import PlainTextResponse, Response
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import os
import aiofiles
import json

from db.database import get_db
from api.routers.auth import get_current_user
from schemas.models import (
    MeetingResponse,
    MeetingDetailResponse,
    MeetingUpdate,
    TranscriptResponse,
    SummaryResponse,
    ActionItemResponse,
)
from services.tasks import process_meeting_audio

from services.utils import get_object_id
from core.constants import ErrorMessages, PaginationLimits, MeetingStatus, ActionItemStatus

router = APIRouter(prefix="/meetings", tags=["meetings"])

UPLOAD_DIR = "uploads/audio"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("", response_model=List[MeetingResponse])
async def list_meetings(
    search: Optional[str] = None,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = {"ownerId": current_user["_id"], "isArchived": {"$ne": True}}
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        transcript_docs = await db.transcripts.find(
            {"content": search_regex}, {"meetingId": 1}
        ).to_list(length=PaginationLimits.MAX_SEARCH_LIMIT)
        transcript_meeting_ids = [
            doc["meetingId"] for doc in transcript_docs if doc.get("meetingId")
        ]
        query["$or"] = [{"title": search_regex}]
        if transcript_meeting_ids:
            query["$or"].append({"_id": {"$in": transcript_meeting_ids}})

    cursor = db.meetings.find(query).sort("recordedAt", -1)
    meetings = await cursor.to_list(length=PaginationLimits.DEFAULT_LIST_LIMIT)

    result = []
    for m in meetings:
        result.append(
            MeetingResponse(
                id=str(m["_id"]),
                title=m.get("title", ""),
                duration=m.get("duration", 0),
                status=m.get("status", MeetingStatus.PROCESSING),
                recordedAt=m.get("recordedAt", datetime.utcnow()),
                notes=m.get("notes"),
            )
        )
    return result


@router.post("", response_model=MeetingDetailResponse)
async def create_meeting(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    duration: int = Form(0),
    audioFile: UploadFile = File(...),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    filename = audioFile.filename if audioFile.filename else "upload.webm"
    file_extension = os.path.splitext(filename)[1]
    if not file_extension:
        file_extension = ".webm"  # default

    file_name = f"{ObjectId()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    # Save file
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await audioFile.read()
        await out_file.write(content)

    # Calculate file size and update user's storage used
    file_size = os.path.getsize(file_path)
    await db.users.update_one(
        {"_id": current_user["_id"]}, {"$inc": {"storageUsed": file_size}}
    )

    now = datetime.utcnow()
    meeting_doc = {
        "ownerId": current_user["_id"],
        "title": title,
        "audioFilePath": f"/uploads/audio/{file_name}",
        "duration": duration,
        "status": MeetingStatus.PROCESSING,
        "recordedAt": now,
        "createdAt": now,
        "isArchived": False,
        "notes": "",
    }

    result = await db.meetings.insert_one(meeting_doc)
    meeting_id = str(result.inserted_id)

    # Trigger background processing
    background_tasks.add_task(process_meeting_audio, meeting_id)

    return MeetingDetailResponse(
        id=meeting_id,
        title=title,
        duration=duration,
        status=MeetingStatus.PROCESSING,
        recordedAt=now,
        notes="",
        audioFilePath=f"/uploads/audio/{file_name}",
    )


@router.get("/{id}/transcript/export")
async def export_transcript(
    id: str,
    format: str = Query("txt", pattern="^(txt|json)$"),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    obj_id = get_object_id(id)

    meeting = await db.meetings.find_one(
        {"_id": obj_id, "ownerId": current_user["_id"], "isArchived": {"$ne": True}}
    )
    if not meeting:
        raise HTTPException(status_code=404, detail=ErrorMessages.MEETING_NOT_FOUND)

    transcript_doc = await db.transcripts.find_one({"meetingId": obj_id})
    if not transcript_doc:
        raise HTTPException(status_code=404, detail=ErrorMessages.TRANSCRIPT_NOT_FOUND)

    safe_title = meeting.get("title", "meeting").strip() or "meeting"
    safe_title = "".join(
        c if c.isalnum() or c in ("-", "_") else "_" for c in safe_title
    )

    if format == "json":
        payload = {
            "meetingId": str(obj_id),
            "title": meeting.get("title", ""),
            "content": transcript_doc.get("content", ""),
            "timestampedSegments": transcript_doc.get("timestampedSegments", []),
            "generatedAt": transcript_doc.get("generatedAt"),
        }
        return Response(
            content=json.dumps(payload, default=str),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_title}_transcript.json"'
            },
        )

    return PlainTextResponse(
        transcript_doc.get("content", ""),
        headers={
            "Content-Disposition": f'attachment; filename="{safe_title}_transcript.txt"'
        },
    )


@router.get("/{id}", response_model=MeetingDetailResponse)
async def get_meeting(
    id: str, db=Depends(get_db), current_user: dict = Depends(get_current_user)
):
    obj_id = get_object_id(id)

    meeting = await db.meetings.find_one(
        {"_id": obj_id, "ownerId": current_user["_id"], "isArchived": {"$ne": True}}
    )
    if not meeting:
        raise HTTPException(status_code=404, detail=ErrorMessages.MEETING_NOT_FOUND)

    # Fetch related records
    transcript_doc = await db.transcripts.find_one({"meetingId": obj_id})
    summary_doc = await db.summaries.find_one({"meetingId": obj_id})

    action_items_cursor = db.actionItems.find(
        {"meetingId": obj_id, "status": {"$ne": ActionItemStatus.ARCHIVED}}
    )
    action_items_docs = await action_items_cursor.to_list(
        length=PaginationLimits.DEFAULT_LIST_LIMIT
    )

    # Format related records
    transcript = None
    if transcript_doc:
        transcript = TranscriptResponse(
            id=str(transcript_doc["_id"]),
            content=transcript_doc.get("content", ""),
            timestampedSegments=transcript_doc.get("timestampedSegments", []),
        )

    summary = None
    if summary_doc:
        summary = SummaryResponse(
            id=str(summary_doc["_id"]),
            summaryText=summary_doc.get("summaryText", ""),
            keyPoints=summary_doc.get("keyPoints", []),
        )

    action_items = []
    for ai in action_items_docs:
        action_items.append(
            ActionItemResponse(
                id=str(ai["_id"]),
                description=ai.get("description", ""),
                status=ai.get("status", ActionItemStatus.PENDING),
                dueDate=ai.get("dueDate"),
                assignee=ai.get("assignee"),
            )
        )

    return MeetingDetailResponse(
        id=str(meeting["_id"]),
        title=meeting.get("title", ""),
        duration=meeting.get("duration", 0),
        status=meeting.get("status", MeetingStatus.PROCESSING),
        recordedAt=meeting.get("recordedAt", datetime.utcnow()),
        notes=meeting.get("notes"),
        audioFilePath=meeting.get("audioFilePath", ""),
        transcript=transcript,
        summary=summary,
        actionItems=action_items if action_items else None,
    )


@router.patch("/{id}", response_model=MeetingResponse)
async def update_meeting(
    id: str,
    item: MeetingUpdate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    obj_id = get_object_id(id)

    meeting = await db.meetings.find_one(
        {"_id": obj_id, "ownerId": current_user["_id"], "isArchived": {"$ne": True}}
    )
    if not meeting:
        raise HTTPException(status_code=404, detail=ErrorMessages.MEETING_NOT_FOUND)

    update_data = {}
    if item.title is not None:
        update_data["title"] = item.title
    if item.notes is not None:
        update_data["notes"] = item.notes

    if update_data:
        await db.meetings.update_one({"_id": obj_id}, {"$set": update_data})

    updated_meeting = await db.meetings.find_one({"_id": obj_id})
    return MeetingResponse(
        id=str(updated_meeting["_id"]),
        title=updated_meeting.get("title", ""),
        duration=updated_meeting.get("duration", 0),
        status=updated_meeting.get("status", MeetingStatus.PROCESSING),
        recordedAt=updated_meeting.get("recordedAt", datetime.utcnow()),
        notes=updated_meeting.get("notes"),
    )


@router.delete("/{id}")
async def archive_meeting(
    id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    obj_id = get_object_id(id)

    res = await db.meetings.update_one(
        {"_id": obj_id, "ownerId": current_user["_id"]}, {"$set": {"isArchived": True}}
    )

    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail=ErrorMessages.MEETING_NOT_FOUND)

    return {"message": "Meeting archived"}
