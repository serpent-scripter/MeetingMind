import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/meetingmind")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Database connection state
class Database:
    client: AsyncIOMotorClient = None

db = Database()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to database
    try:
        db.client = AsyncIOMotorClient(MONGODB_URI)
        print("Connected to MongoDB.")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
    yield
    # Disconnect
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB.")

app = FastAPI(title="MeetingMind API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")

@app.get("/healthz", tags=["health"])
async def healthz():
    db_status = "disconnected"
    if db.client:
        try:
            await db.client.admin.command('ping')
            db_status = "connected"
        except Exception:
            db_status = "error"
    return {"status": "ok", "db": db_status}

# Include routers here later
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
