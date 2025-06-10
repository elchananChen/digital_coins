# db_worker.py
import asyncio
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv


from beanie import init_beanie
from core import init_redis_client, init_db
from motor.motor_asyncio import AsyncIOMotorClient

import redis.asyncio as redis

from core import OrderBook
load_dotenv()

# הגדרות Batching (תצטרך לכוונן אותן!)
BATCH_SIZE = 100 # מספר המסמכים לאגור לפני כתיבה
GLOBAL_BATCH_SIZE = 500 
FLUSH_INTERVAL = timedelta(milliseconds=200) # זמן מקסימלי לחכות לפני כתיבה (גם אם ה-batch לא מלא)

# באפר לנתונים וזמנים אחרונים לכל צמד מטבע/בורסה
# defaultdict מאפשר גישה למפתח שאינו קיים ומחזיר ערך ברירת מחדל (רשימה ריקה במקרה זה)
data_buffer = {} # ישתמש במילון רגיל ולא defaultdict כדי לנהל זמנים
last_flush_time = {}

async def flush_data(redis_client, key: str):
    """Writes accumulated data for a specific key (exchange@symbol) to MongoDB."""
    if not key in data_buffer or not data_buffer[key]:
        return # אין נתונים ל-flush עבור מפתח זה
    documents_to_insert_snapshot = list(data_buffer[key])
    data_buffer[key].clear()  
    last_flush_time[key] = datetime.now() # אפס את טיימר הפלאש
    try:
        # שימוש ב-insert_many של Beanie
        await OrderBook.insert_many(documents_to_insert_snapshot)
        print(f"Flushed {len(documents_to_insert_snapshot)} documents for {key} to MongoDB.")
    except Exception as e:
        print(f"Error flushing data for {key} to MongoDB: {e}")
        # לוגיקת טיפול בשגיאות: ניסיון חוזר, שליחה ל-DLQ, וכו'
    
        



async def process_redis_queue(redis_client: redis.Redis):
    """Continuously processes messages from the Redis queue."""
    print("DB Worker started, listening to Redis queue...")

    pending_flush_tasks = []
    while True:
        try:
            # BLPOP חוסמת עד שיש אלמנט בתור. ה-0 פירושו חכה בלי הגבלת זמן.
            # הוא מחזיר tuple של שם הרשימה והאלמנט.
            # ייתכן שתרצה להשתמש ב-XREAD/XREADGROUP עבור Redis Streams אם תבחר בזה
            # אך BLPOP יעיל עבור רשימות פשוטות

            _ , json_data_str = await redis_client.blpop("order_book_updates", 0)

         
            decoded_data = json.loads(json_data_str)

            # extract the exchange and symbol for the key
            exchange_name = decoded_data.get("exchange")
            symbol = decoded_data.get("symbol")

            if not (exchange_name and symbol):
                print(f"Skipping malformed data: {decoded_data}")
                continue

            key = f"{symbol}@{exchange_name}"

            if key not in data_buffer:
                data_buffer[key] = []
                last_flush_time[key] = datetime.now()

            data_buffer[key].append(decoded_data) 

            # --- check the bach size condition for each symbol---
            if len(data_buffer[key]) >= BATCH_SIZE:
                pending_flush_tasks.append(asyncio.create_task(flush_data(redis_client, key)))
            
            # --- check the global bach size condition  ---
            total_buffered_items = sum(len(lst) for lst in data_buffer.values())
            if total_buffered_items >= GLOBAL_BATCH_SIZE:
                print(f"Global batch size reached ({total_buffered_items} items). Flushing all buffers.")
                # flush all the coins
                keys_to_flush_globally = list(data_buffer.keys())
                for k in keys_to_flush_globally:
                    if data_buffer[k]:
                        pending_flush_tasks.append(asyncio.create_task(flush_data(redis_client, k)))
            if pending_flush_tasks:
                # Use gather to run all collected flush tasks concurrently
                results = await asyncio.gather(*pending_flush_tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        print(f"A flush task failed: {res}")

                # clear the pending_flush_tasks
                pending_flush_tasks = [] 


        except Exception as e:
            print(f"Error in DB Worker processing loop: {e}")
            await asyncio.sleep(1) 


# --- independent process for time limit  ---
async def periodic_time_flush(redis_client: redis.Redis):
    """Periodically checks all buffers and flushes data based on FLUSH_INTERVAL."""
    print("Periodic time flush task started.")
    while True:
        try:
            await asyncio.sleep(FLUSH_INTERVAL.total_seconds() / 2) # Check more frequently than flush interval
            current_time = datetime.now()
            # Create a copy of keys to iterate over, as data_buffer might change during iteration
            keys_to_check_for_time = list(data_buffer.keys())
            
            tasks_to_run = []
            for k in keys_to_check_for_time:
                # Ensure the buffer exists and is not empty, and time condition is met
                if k in data_buffer and data_buffer[k] and \
                   (current_time - last_flush_time[k]) > FLUSH_INTERVAL:
                    
                    # Create a task for each flush and add to a list
                    tasks_to_run.append(asyncio.create_task(flush_data(redis_client, k)))
            
            if tasks_to_run:
                # Run all time-based flush tasks concurrently
                results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        print(f"A periodic time flush task failed: {res}")

        except asyncio.CancelledError:
            print("Periodic time flush task cancelled.")
            break # Exit loop cleanly
        except Exception as e:
            print(f"Error in periodic_time_flush: {e}")
            await asyncio.sleep(1) # Prevent tight loop on error


async def main():
    redis_client = await init_redis_client()
    if not redis_client:
        print("Failed to connect to Redis for DB Worker. Exiting.")
        return   
    
    db_client = await init_db()
    if not db_client: # חשוב לבדוק אם החיבור ל-DB נכשל
        print("Failed to connect to MongoDB. Exiting.")

    #  A separate task for flushing based on FLUSH_INTERVAL
    # This task will run independently and periodically check for time-based flushes
    time_flush_task = asyncio.create_task(periodic_time_flush(redis_client))

    # Start the main queue processing
    await process_redis_queue(redis_client)

    # Clean up (usually not reached in an infinite loop, but good for graceful shutdown)
    time_flush_task.cancel() 
    try:
        await time_flush_task
    except asyncio.CancelledError:
        pass

    if redis_client:
        await redis_client.close()
        print("Redis connection closed.")
    if db_client:
        db_client.close()
        print("MongoDB connection closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("DB Worker stopped by user.")
    except asyncio.CancelledError:
        print("DB Worker task cancelled.")