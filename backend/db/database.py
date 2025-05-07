from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from fastapi import HTTPException

from core.constants import ErrorMessages


class Database:
    client: Optional[AsyncIOMotorClient] = None

    @property
    def db(self):
        if self.client:
            return self.client.get_default_database()
        return None


db_state = Database()


def get_db():
    if db_state.db is None:
        raise HTTPException(
            status_code=500, detail=ErrorMessages.DATABASE_NOT_CONNECTED
        )
    return db_state.db
