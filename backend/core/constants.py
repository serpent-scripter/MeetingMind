class ErrorMessages:
    INVALID_ID_FORMAT = "Invalid ID format"
    DATABASE_NOT_CONNECTED = "Database not connected"
    MEETING_NOT_FOUND = "Meeting not found"
    ACTION_ITEM_NOT_FOUND = "Action item not found"
    TRANSCRIPT_NOT_FOUND = "Transcript not found"
    USER_NOT_FOUND = "User not found"
    CREDENTIALS_VALIDATION_FAILED = "Could not validate credentials"
    EMAIL_ALREADY_REGISTERED = "Email already registered"
    INCORRECT_EMAIL_PASSWORD = "Incorrect email or password"


class PaginationLimits:
    DEFAULT_LIST_LIMIT = 100
    MAX_SEARCH_LIMIT = 1000


class MeetingStatus:
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    ARCHIVED = "archived"


class ActionItemStatus:
    PENDING = "pending"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AIModels:
    ASSEMBLYAI_SPEECH_MODEL = "universal-2"
    GROQ_LLM_MODEL = "llama-3.1-8b-instant"


class SecurityConstants:
    JWT_ALGORITHM = "HS256"
