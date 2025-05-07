import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from db.database import db_state
from api.routers import auth, meetings, actions, users
from core.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/meetingmind")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Ensure upload directory exists
os.makedirs("uploads/audio", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to database
    try:
        db_state.client = AsyncIOMotorClient(MONGODB_URI)
        logger.info("Connected to MongoDB.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
    yield
    # Disconnect
    if db_state.client:
        db_state.client.close()
        logger.info("Disconnected from MongoDB.")


app = FastAPI(
    title="MeetingMind API",
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

api_router = APIRouter(prefix="/api/v1")


@api_router.get("", include_in_schema=False)
@api_router.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/api/v1/docs")


@app.get("/healthz", tags=["health"])
async def healthz():
    db_status = "disconnected"
    if db_state.client:
        try:
            await db_state.client.admin.command("ping")
            db_status = "connected"
        except Exception:
            db_status = "error"
    return {"status": "ok", "db": db_status}


api_router.include_router(auth.router)
api_router.include_router(meetings.router)
api_router.include_router(actions.router)
api_router.include_router(users.router)

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
