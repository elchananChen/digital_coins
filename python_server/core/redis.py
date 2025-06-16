import redis
import os
from dotenv import load_dotenv
from datetime import datetime
# for typing
import redis.asyncio as redis

load_dotenv()

# Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

async def init_redis_client():
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True
        )

        await redis_client.ping()
        print("Connected to Redis successfully.")
        return redis_client
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        return None


async def send_to_redis_queue(redis_client: redis.Redis, json_data: str,symbol:str, exchange_name,update_tracker,tracker:dict):
    try:
        # print("REDIS pre push")
        before = datetime.now()
        await redis_client.rpush("order_book_updates", json_data)
        insert_time = datetime.now() - before
        update_tracker(tracker,symbol,1,insert_time.microseconds)
        # print(f"Sent order book update for {symbol}@{exchange_name} to Redis.")
    except Exception as e:
        print(f"Error sending to Redis: {e}")
