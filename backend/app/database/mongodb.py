"""MongoDB connection management"""
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from ..config import settings


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


mongodb = MongoDB()


async def connect_to_mongo() -> None:
    mongodb.client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=2000)
    mongodb.db = mongodb.client[settings.mongodb_db_name]


async def close_mongo_connection() -> None:
    if mongodb.client is not None:
        mongodb.client.close()


def get_database() -> AsyncIOMotorDatabase:
    if mongodb.db is None:
        raise RuntimeError("MongoDB is not connected. Call connect_to_mongo() first.")
    return mongodb.db


async def ping_mongo() -> bool:
    if mongodb.client is None:
        return False
    try:
        await mongodb.client.admin.command("ping")
        return True
    except Exception:
        return False
