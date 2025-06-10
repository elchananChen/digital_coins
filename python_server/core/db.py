from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from core.models import OrderBook 
import os
from dotenv import load_dotenv

load_dotenv()

DB_URI = os.getenv("DB_URI")
DB_NAME = os.getenv("DB_NAME", "digitalCoins")

async def init_db():
    client = AsyncIOMotorClient(DB_URI)
    await init_beanie(database=client[DB_NAME], document_models=[OrderBook])
    print("successfully connect to db")
    return client