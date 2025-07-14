import redis
import os

import redis.asyncio as redis

from utils import log_and_categorize_redis_error


async def init_redis_client():
    try:
        REDIS_HOST = os.getenv('REDIS_HOST')
        REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
        REDIS_DB = int(os.getenv('REDIS_DB', 0))
        REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True
        )

        await redis_client.ping()
        print(f"REDIS_HOST: {REDIS_HOST}")
        print("Connected to Redis successfully.")
        return redis_client
    except Exception as e:
        print(REDIS_HOST)
        print(f"Failed to connect to Redis: {e}")
        return None


async def send_to_redis_queue(redis_client: redis.Redis, json_data: str,symbol:str, exchange_name, error_summary:dict):
    try:
        await redis_client.rpush("order_book_updates", json_data)
        return 1
    except Exception as e:
        log_and_categorize_redis_error(e=e,symbol=symbol,exchange=exchange_name,error_summary=error_summary)
        return 0
