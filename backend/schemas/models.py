from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class SignupResponse(BaseModel):
    email: str
    name: str
    storageUsed: int = 0


class LoginResponse(BaseModel):
    access_token: str


class LogoutResponse(BaseModel):
    message: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    storageUsed: int = 0


class MeetingResponse(BaseModel):
    id: str
    title: str
    duration: int
    status: str
    recordedAt: datetime
    notes: Optional[str] = None


class TranscriptSegment(BaseModel):
    start: int
    end: int
    text: str
    speaker: Optional[str] = None


class TranscriptResponse(BaseModel):
    id: str
    content: str
    timestampedSegments: List[TranscriptSegment]


class SummaryResponse(BaseModel):
    id: str
    summaryText: str
    keyPoints: List[str]


class ActionItemResponse(BaseModel):
    id: str
    description: str
    status: str
    dueDate: Optional[datetime] = None
    meetingId: Optional[str] = None
    assignee: Optional[str] = None


class ActionItemCreate(BaseModel):
    meetingId: str
    description: str
    assignee: Optional[str] = None


class ActionItemUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    dueDate: Optional[datetime] = None
    assignee: Optional[str] = None


class MeetingDetailResponse(MeetingResponse):
    audioFilePath: str
    transcript: Optional[TranscriptResponse] = None
    summary: Optional[SummaryResponse] = None
    actionItems: Optional[List[ActionItemResponse]] = None


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    notes: Optional[str] = None
