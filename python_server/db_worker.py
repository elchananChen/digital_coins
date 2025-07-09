import logging
import time
import redis
import asyncio
import json 

from datetime import datetime, timedelta
from typing import List,Literal
from dotenv import load_dotenv

from monitoring.models import ErrorDetails, DBWorkerBatchFlushEvent
from monitoring.utils import send_metric_log,send_heartbeat

from core import OrderBook # Assuming OrderBook is a Beanie document/Pydantic model
from core.db import init_db
from core.redis import init_redis_client

load_dotenv()

logger = logging.getLogger("db_worker")

# --- Batching and Flushing Configuration ---
BATCH_SIZE = 50 # Number of documents to accumulate per key (exchange@symbol) before writing
GLOBAL_BATCH_SIZE = 400 # Total number of documents across all keys to accumulate before a global flush
FLUSH_INTERVAL = timedelta(milliseconds=200) # Maximum time to wait before writing (even if batch isn't full)

# --- Data Buffers and Trackers ---

# Tracker for inserts for debugging/monitoring purposes
# Format: {key: [total_inserted_count, last_insert_datetime, [last_batch_size, last_insert_duration_microseconds]]}
insert_tracker = {}

# Buffer for accumulating data before writing to MongoDB
# Uses a regular dictionary to manage last_flush_time per key
data_buffer = {} 
last_flush_time = {} # Stores the last time data was flushed for a specific key


def update_insert_tracker(tracker: dict, key: str, insert_number: int, insert_time: int):
    """
    Updates the insert tracker with the number of documents inserted and the time taken.
    """
    if key not in tracker:        
        tracker[key] = [insert_number, datetime.now(), [insert_number, insert_time]]
    else:        
        # tracker[key].append([insert_number,insert_time]) # This line was commented out in original, so keeping it commented.
        tracker[key][0] += insert_number # Accumulate total inserts
        tracker[key][1] = datetime.now() # Update last insert time
        tracker[key][2] = [insert_number, insert_time] # Store last batch size and duration


async def flush_data( key: str,event_type:Literal["batch_flush", "global_flush", "time_flush"]):
    """
    Writes accumulated data for a specific key (e.g., 'symbol@exchange') to MongoDB.
    Clears the buffer for that key after successful insertion.
    """
    if not key in data_buffer or not data_buffer[key]:
        return

    documents_to_insert_snapshot: List[OrderBook] = []
    # Convert dictionary data from buffer into OrderBook Beanie/Pydantic objects
    for doc_dict in data_buffer[key]:
        try:
            documents_to_insert_snapshot.append(OrderBook(**doc_dict))
        except Exception as e:
            logger.error(f"Error creating OrderBook object from dict (key: {key}): {e}")
            continue 

    # for monitoring 
    buffer_size_before_flush =len(data_buffer.get(key, []))
    documents_count = len(documents_to_insert_snapshot)
    flush_status = "failure"
    flush_error_details = None
    start_time = time.monotonic() 
    
    # Clear the buffer and update the last flush time immediately
    # This is done before the DB write to prevent re-flushing the same data
    # if an error occurs during insertion (though it might lead to data loss on crash).
    data_buffer[key].clear()
    last_flush_time[key] = datetime.now()

    if not documents_to_insert_snapshot: 
        logger.info(f"No valid documents to flush for {key} after processing.")
        return

    try:
        before_insert = datetime.now()
        await OrderBook.insert_many(documents_to_insert_snapshot)
        insert_duration = datetime.now() - before_insert
        update_insert_tracker(insert_tracker, key, len(documents_to_insert_snapshot), insert_duration.microseconds)
        logger.info(f"Flushed {len(documents_to_insert_snapshot)} documents for {key} to MongoDB.")
        flush_status = "success"
    except Exception as e:
        logger.error(f"Error flushing data for {key} to MongoDB: {e}")
        flush_error_details = ErrorDetails(
            error_code=type(e).__name__,
            error_message=str(e),
            is_critical=True
            )
        # Error handling logic: retry, send to Dead Letter Queue (DLQ), etc.
    finally:
        flush_duration_ms = (time.monotonic() - start_time) * 1000
        send_metric_log(
            DBWorkerBatchFlushEvent(
                event_type=event_type,
                key=key,
                documents_count=documents_count,
                flush_duration_ms=flush_duration_ms,
                status=flush_status,
                error_details=flush_error_details,
                buffer_size_before_flush=buffer_size_before_flush
            )
        )


async def process_redis_queue(redis_client: redis.Redis):
    """
    Continuously processes messages from the Redis queue.
    Buffers messages and triggers flushes based on batch size conditions.
    """
    print("DB Worker started, listening to Redis queue...")

    pending_flush_tasks = [] # List to hold asyncio tasks for flushing data
    while True:
        try:
            # BLPOP blocks until an element is available in the list.
            # 0 means wait indefinitely.
            # It returns a tuple of (list_name, element).
            # For more advanced scenarios, Redis Streams (XREAD/XREADGROUP) might be preferred,
            # but BLPOP is efficient for simple list queues.
            _, json_data_str = await redis_client.blpop("order_book_updates", 0)

            decoded_data = json.loads(json_data_str)

            # Extract exchange and symbol to create a unique key for buffering
            exchange_name = decoded_data.get("exchange")
            symbol = decoded_data.get("symbol")

            if not (exchange_name and symbol):
                logger.error(f"Skipping malformed data: {decoded_data}")
                continue

             # e.g., "BTCUSD@binance"
            key = f"{symbol}@{exchange_name}"

            # Initialize buffer and last flush time for new keys
            if key not in data_buffer:
                data_buffer[key] = []
                last_flush_time[key] = datetime.now()

            data_buffer[key].append(decoded_data) 

            # --- Check batch size condition for each specific key ---
            if len(data_buffer[key]) >= BATCH_SIZE:
                pending_flush_tasks.append(asyncio.create_task(flush_data(key=key, event_type="batch_flush")))

            # --- Check the global batch size condition across all buffers ---
            total_buffered_items = sum(len(lst) for lst in data_buffer.values())
            if total_buffered_items >= GLOBAL_BATCH_SIZE:
                logger.info(f"Global batch size reached ({total_buffered_items} items). Flushing all buffers.")
                # Trigger flush for all non-empty buffers
                # Iterate over a copy of keys
                keys_to_flush_globally = list(data_buffer.keys())
                for k in keys_to_flush_globally:
                    # Only flush if there's actual data
                    if data_buffer[k]:
                        pending_flush_tasks.append(asyncio.create_task(flush_data(key=k, event_type="global_flush")))

            # If there are any pending flush tasks (from batch conditions), run them concurrently
            if pending_flush_tasks:
                results = await asyncio.gather(*pending_flush_tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        print(f"A flush task failed: {res}")
                pending_flush_tasks = [] # Clear the list of pending tasks


        except Exception as e:
            print(f"Error in DB Worker processing loop: {e}")
            await asyncio.sleep(1) # Wait before retrying to prevent a tight loop on continuous errors


# --- Independent Task for Time-based Flushing ---
async def periodic_time_flush(redis_client: redis.Redis):
    """
    Periodically checks all data buffers and flushes data to MongoDB
    if the FLUSH_INTERVAL has elapsed since the last flush for that key.
    """
    print("Periodic time flush task started.")
    while True:
        try:
            # Sleep for half the flush interval to check more frequently
            await asyncio.sleep(FLUSH_INTERVAL.total_seconds() / 2) 
            current_time = datetime.now()
            
            # Create a copy of keys to iterate over, as data_buffer might be modified
            # by concurrent flush tasks or the main processing loop
            keys_to_check_for_time = list(data_buffer.keys())
            
            tasks_to_run = []
            for k in keys_to_check_for_time:
                # Check if buffer exists, is not empty, and the time condition is met
                if k in data_buffer and data_buffer[k] and \
                   (current_time - last_flush_time.get(k, datetime.min)) > FLUSH_INTERVAL: # Use datetime.min for keys not yet in last_flush_time
                    
                    tasks_to_run.append(asyncio.create_task(flush_data(key=k, event_type="time_flush")))

            if tasks_to_run:
                # Run all time-based flush tasks concurrently
                results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        logger.error(f"A periodic time flush task failed: {res}")

        except asyncio.CancelledError:
            logger.info("Periodic time flush task cancelled.")
            break # Exit the loop cleanly if the task is cancelled
        except Exception as e:
            logger.error(f"Error in periodic_time_flush: {e}")
            await asyncio.sleep(1) # Prevent a tight loop on error


async def main():
    """
    Main entry point for the DB Worker.
    Initializes Redis and MongoDB connections, then starts the data processing loops.
    """
    redis_client = await init_redis_client()
    if not redis_client:
        logger.critical("🛑 Failed to connect to Redis for DB Worker. Exiting.")
        return
    
    db_client = await init_db()
    if not db_client: 
        logger.critical("🛑 Failed to connect to MongoDB. Exiting.")
        return 

    # heartbeat monitor
    heartbeat_task = asyncio.create_task(
        send_heartbeat(
            data_buffer=data_buffer,
            interval_seconds=30,
            last_flush_time=last_flush_time,
            redis_client=redis_client,
            logger=logger
            ))

    # Start a separate background task for time-based flushing
    time_flush_task = asyncio.create_task(periodic_time_flush(redis_client))
    main_task = asyncio.create_task(process_redis_queue(redis_client))
    try:
        await asyncio.gather(main_task,time_flush_task, heartbeat_task,)
    except asyncio.CancelledError:
        logger.info("Main tasks cancelled gracefully.")
    except Exception as e:
        logger.critical(f"An unhandled exception occurred in main tasks: {e}", exc_info=True)
    finally:
        heartbeat_task.cancel() 
        time_flush_task.cancel()
        
        try:
            await asyncio.gather(heartbeat_task, time_flush_task, return_exceptions=True)
        except asyncio.CancelledError:
            pass 
        
        if redis_client:
            await redis_client.close()
            logger.info("Redis connection closed.")
        if db_client:
            db_client.close() 
            logger.info("MongoDB connection closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(insert_tracker) # Print the tracker on manual shutdown
        logger.info("DB Worker stopped by user.")
    except asyncio.CancelledError:
        logger.info("DB Worker task cancelled.")
