from beanie import Document
from pydantic import BaseModel
from datetime import datetime
from typing import List
from pymongo import IndexModel, ASCENDING, DESCENDING
import os

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ScrapingOrderBook")

class Order(BaseModel):
    price: str
    amount: str

class OrderBook(Document):
    symbol: str
    exchange: str
    timestamp: datetime
    bids: List[Order]
    asks: List[Order]

    class Settings:
        name = COLLECTION_NAME
        indexes = [
            # IndexModel([("timestamp", ASCENDING)], expireAfterSeconds=600),
            IndexModel([("symbol", ASCENDING), ("exchange", ASCENDING), ("timestamp", DESCENDING)])
        ]
