import redis
import os
from dotenv import load_dotenv


# for typing
import redis.asyncio as redis

# error handlers from utils
from utils import log_and_categorize_redis_error


load_dotenv()

async def init_redis_client():
    try:

        # Redis
        REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
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
        print("Connected to Redis successfully.")
        return redis_client
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        return None


async def send_to_redis_queue(redis_client: redis.Redis, json_data: str,symbol:str, exchange_name, error_summary:dict):
    try:
        # print("REDIS pre push")
        await redis_client.rpush("order_book_updates", json_data)
        return 1
        # print(f"Sent order book update for {symbol}@{exchange_name} to Redis.")
    except Exception as e:
        log_and_categorize_redis_error(e=e,symbol=symbol,exchange=exchange_name,error_summary=error_summary)
        return 0
