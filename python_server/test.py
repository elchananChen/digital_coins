# dates
from datetime import datetime, timezone
from time import time

# python
import json 
import asyncio
import os

# utils functions - REMOVE OLD ERROR HANDLERS FROM HERE
# The error handlers are now in 'errors_handlers.py' and return ErrorDetails objects.
from utils import (
    merge_addition_dicts,
    add_overall_exchange_status
    )

# NEW: Import functions from the updated errors_handlers.py
from utils.error_handlers import (
    create_playwright_error_details,
    create_general_exception_details,
    create_websocket_data_error_details,
    create_redis_error_details
)

# monitoring utils
from monitoring.utils import (
    time_async_function,
    handle_async_errors
)
from lists.bit_stamp_lists import bit_stamp_symbols

from monitoring.models import ExchangeScrapeReport, ExchangeCurrencyEvent, EventTypeEnum # NEW: Import ExchangeCurrencyEvent, EventTypeEnum for granular error reporting

# playwright
from playwright._impl._errors import Error as PlaywrightError # Recommended alias

# for errors track
import logging

# redis 
from core import send_to_redis_queue # Assuming this is your original Redis send function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_bit_stamp_coin_order_book(bit_stamp_symbol, db_symbol, context,redis_client,exchange_name, event:asyncio.Event,sleep_time=0):
    local_send_to_redis = 0
    local_errors_summary = {} # This will continue to collect counts of error_codes
    page = None

    # --- Variables to pass state to finally block ---
    final_status = "failure" # Assume failure until proven otherwise

    try:
        page = await context.new_page()
        page_created_successfully = True # Flag to indicate if page was created
        first_payload_for_channel = True

        #   socket definition
        def on_websocket(ws):
                # for catching the payload
                # will be overwrite every half a second 
                order_books_string = ""
                
                async def process_data():
                    try:         
                        nonlocal final_status               
                        nonlocal local_send_to_redis
                        nonlocal order_books_string
    
                        # Convert to json
                        json_data = json.loads(order_books_string)

                        if "data" not in json_data:
                            # Use new error handler
                            error_details = create_websocket_data_error_details(
                                e=ValueError("Received empty data payload"),
                                symbol=db_symbol,
                                exchange=exchange_name, 
                                is_empty_data_error=True
                                )
                            local_errors_summary[error_details.error_code] = local_errors_summary.get(error_details.error_code, 0) + 1
                            return
                        
                        json_data_keys = ["asks","bids", "timestamp"]
                        for key in json_data_keys:
                            if key  not in json_data["data"]:
                                # Use new error handler
                                error_details = create_websocket_data_error_details(
                                    e=KeyError("Missing keys in payload data"),
                                    symbol=db_symbol,
                                    exchange=exchange_name,
                                    is_missing_keys_error=True
                                    )
                                local_errors_summary[error_details.error_code] = local_errors_summary.get(error_details.error_code, 0) + 1
                                return
    
                        data = json_data["data"]
                        origin_asks = data["asks"]
                        origin_bids = data["bids"]
                        origin_time = int(data["timestamp"])
    
                        # Validate that asks and bids have proper structure
                        if not origin_asks and not origin_bids:
                            # Use new error handler
                            error_details = create_websocket_data_error_details(
                                e=ValueError("Received empty asks and bids data"),
                                symbol=db_symbol,
                                exchange=exchange_name,
                                is_validation_error=True
                                )
                            local_errors_summary[error_details.error_code] = local_errors_summary.get(error_details.error_code, 0) + 1
                            return
    
                        # Convert to datetime in UTC format
                        datetime_utc = datetime.fromtimestamp(origin_time, tz=timezone.utc)
                        timestamp = datetime_utc.isoformat(timespec='milliseconds')
    
                        data =  { "symbol": db_symbol,"exchange": exchange_name,"timestamp": timestamp , "bids": origin_bids,"asks": origin_asks }
                        data_as_string = json.dumps(data)
                        
                        # Assuming send_to_redis_queue might still take error_summary for its internal reporting if needed,
                        # but ideally, it should also be refactored to return ErrorDetails if it catches exceptions.
                        # For now, if send_to_redis_queue itself uses the old error_summary logic, we keep it.
                        res = await send_to_redis_queue(redis_client, data_as_string, db_symbol,exchange_name,error_summary=local_errors_summary)
    
                        # for monitor
                        if res >= 1:
                            final_status = "success"
                        local_send_to_redis += res # res = 1 / 0
                    except Exception as e:
                        # Use new error handler for general websocket processing errors
                        error_details = create_websocket_data_error_details(
                            e=e,
                            symbol=db_symbol,
                            exchange=exchange_name
                            )
                        local_errors_summary[error_details.error_code] = local_errors_summary.get(error_details.error_code, 0) + 1

                # every time the data come - will be assign to current time
                # for control of the data processing timing without interrupt the frame listening process.
                last_save_time = 0

                async def on_frame_received(payload: str):
                    nonlocal first_payload_for_channel
                    nonlocal order_books_string 
                    nonlocal last_save_time

                    now = time()

                    if now - last_save_time >= 1:
                        if f'"channel":"order_book_{bit_stamp_symbol}"' in payload:
                            # return if first payload because it empty
                            if first_payload_for_channel:
                                first_payload_for_channel = False
                                return
                            order_books_string = payload
                            last_save_time = now
                            asyncio.create_task(process_data())
                ws.on("framereceived", on_frame_received)

        # add the socket listening to the page
        page.on("websocket", on_websocket)
        await asyncio.sleep(sleep_time)

        await page.goto(f"https://www.bitstamp.net/trade/{bit_stamp_symbol}", wait_until="domcontentloaded")
        logger.info(f"🫡 {bit_stamp_symbol} go to page")
        await event.wait() 
    
    except PlaywrightError as e:
        # Use new error handler
        # Ensure page_created_successfully is correctly set (initialized to True, then confirmed/denied)
        error_details = create_playwright_error_details(e=e,symbol=db_symbol,page_created=page_created_successfully )
        local_errors_summary[error_details.error_code] = local_errors_summary.get(error_details.error_code, 0) + 1
        # Optional: send a specific event for this
        # send_metric_log(ExchangeCurrencyEvent(
        #     currency_pair=db_symbol, exchange_name=exchange_name, event_name="playwright_page_error",
        #     event_type=EventTypeEnum.error, error_details=error_details))

        # Original screenshot logic (remains as is)
        try:
            screenshot_dir = "debug_screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, f"{db_symbol}_playwright_error_{int(time())}.png")
            await page.screenshot(path=screenshot_path)
            logger.info(f"📸 {db_symbol}: Screenshot taken for Playwright error at {screenshot_path}.")
        except PlaywrightError as ss_e:
            if page and not page.is_closed(): # Check if page exists and isn't already closed
                await page.close()
                print("😇")
                logger.info(f"🔚 Closed page for {bit_stamp_symbol}")
        except Exception as e:
            print("😇")
            logger.error(f"❌ Error closing page for {bit_stamp_symbol}: {e}")

    except Exception as e:
        # Use new error handler for general exceptions
        error_details = create_general_exception_details(e=e,symbol=db_symbol)
        local_errors_summary[error_details.error_code] = local_errors_summary.get(error_details.error_code, 0) + 1
        # Optional: send a specific event for this
        # send_metric_log(ExchangeCurrencyEvent(
        #     currency_pair=db_symbol, exchange_name=exchange_name, event_name="general_scraper_exception",
        #     event_type=EventTypeEnum.error, error_details=error_details))

    finally:
        if page:
            try:
                await page.close() # Always try to close the page if it was created
                print("🙃")
                logger.info(f"🔚 Closed page for {bit_stamp_symbol}")
            except Exception as e: # Catch errors specifically during page.close()
                print("🙃")
                logger.error(f"❌ Error closing page for {bit_stamp_symbol}: {e}")

        return {
            "pair_name": db_symbol,
            "local_send_to_redis":local_send_to_redis,
            "local_errors_summary": local_errors_summary,
            "status": final_status,
        }


# all coins running together in the same time
#  but! initial the process after some time for each batch
@time_async_function(component_name="scraper_run", event_name="exchange_scrape_duration")
@handle_async_errors(component_name="scraper_run", is_critical=True)
async def run_bit_stamp_scraper_redis(context , redis_client,exchange_name,event,delay_per_task): 
    monitor_data = {
        "total_currency_pairs_configured": len(bit_stamp_symbols),
        "successful_currency_pair_initializations": 0,
        "failed_currency_pair_initializations":0,

        # --- Data Volume and Quality Metrics ---
        "total_data_points_sent_to_redis":0,
        "errors_summary":{} # This will aggregate all error codes from individual tasks
    }

    tasks = []
    results = []
    logger.info(f"Total symbols: {len(bit_stamp_symbols)}")
   
    for i, (db_symbol,bit_stamp_symbol) in enumerate(bit_stamp_symbols.items()):
        sleep_time = i * delay_per_task
        task = asyncio.create_task(
            get_bit_stamp_coin_order_book(
                bit_stamp_symbol, 
                db_symbol, 
                context, 
                redis_client,
                exchange_name,
                event=event,
                sleep_time=sleep_time
                  ))
        tasks.append(task)
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
       
    except asyncio.exceptions.CancelledError:
        logger.info("❌ Scraper run was cancelled.")
        # If the whole run is cancelled, consider this a planned shutdown
        # and update the overall status accordingly in monitor_data before creating report
        monitor_data["status"] = "planned_shutdown"
 
    except Exception as e:
        logger.error(f"🔴 Uncaught critical exception in run_bit_stamp_scraper_redis: {e}", exc_info=True)
        # Use new error handler for uncaught critical exceptions
        error_details = create_general_exception_details(e=e, symbol="OVERALL_RUN_ERROR")
        monitor_data["errors_summary"][error_details.error_code] = monitor_data["errors_summary"].get(error_details.error_code, 0) + 1
        monitor_data["status"] = "unplanned_shutdown" # Mark as unplanned shutdown due to fatal error
        # Optional: send a specific event for this critical error
        # send_metric_log(ExchangeCurrencyEvent(
        #     currency_pair="N/A", exchange_name=exchange_name, event_name="fatal_scraper_run_error",
        #     event_type=EventTypeEnum.error, error_details=error_details))
        
    finally:
        for res in results:
            # if proper monitor data return and local_send... in it - add it to monitor_data
            if isinstance(res, dict) and "local_send_to_redis" in res:
                monitor_data["total_data_points_sent_to_redis"] += res["local_send_to_redis"]

            if isinstance(res,dict) and "local_errors_summary" in res \
                and isinstance(res["local_errors_summary"],dict):
                merged_data = merge_addition_dicts(res["local_errors_summary"], monitor_data["errors_summary"])
                monitor_data["errors_summary"] = merged_data

            if isinstance(res,dict) and "status" in res:
                # if points send or not to redis for this currency pair
                if res["status"] == "failure":
                    monitor_data["failed_currency_pair_initializations"] += 1
                    logger.error(f"🔴 no points send to redis for: {res['pair_name']}")
                elif res["status"] == "success":
                    monitor_data["successful_currency_pair_initializations"] += 1

            elif isinstance(res, Exception): # This means an exception escaped get_bit_stamp_coin_order_book entirely
                monitor_data["failed_currency_pair_initializations"] += 1
                logger.error(f"🔴 Critical exception escaped task for a scraper: {type(res).__name__}: {res}", exc_info=True)
                # Use new error handler for escaped exceptions
                error_details = create_general_exception_details(e=res, symbol="ESCAPED_TASK_ERROR")
                monitor_data["errors_summary"][error_details.error_code] = monitor_data["errors_summary"].get(error_details.error_code, 0) + 1
                # Optional: send a specific event for this
                # send_metric_log(ExchangeCurrencyEvent(
                #     currency_pair="N/A", exchange_name=exchange_name, event_name="escaped_task_error",
                #     event_type=EventTypeEnum.error, error_details=error_details))

        add_overall_exchange_status(monitor_data) # This function will set final_status based on errors_summary etc.

        logger.info(monitor_data)
        # Assuming monitor_data["status"] holds the CloseStatusEnum value correctly after add_overall_exchange_status
        final_close_status = monitor_data.get("status", "planned_shutdown") # Default to planned if not set

        return ExchangeScrapeReport(
           exchange_name=exchange_name,
           overall_exchange_status=final_close_status, # Use the string status from monitor_data
           total_currency_pairs_configured=monitor_data["total_currency_pairs_configured"],
           successful_currency_pair_initializations=monitor_data["successful_currency_pair_initializations"],
           failed_currency_pair_initializations=monitor_data["failed_currency_pair_initializations"],
           total_data_points_sent_to_redis=monitor_data["total_data_points_sent_to_redis"],
           errors_summary=monitor_data["errors_summary"]
        )


# import asyncio


# event = asyncio.Event()


# async def waiter(num):
#     print("Waiting...")
#     await event.wait()
#     print(f"Event {num} is set!")

# async def main():
#     tasks =[]
#     for i in range(2):
#         task = asyncio.create_task(waiter(i+1))
#         tasks.append(task)

#     await asyncio.sleep(4)
#     event.set()
#     await asyncio.gather(*tasks)

# asyncio.run(main())

# #  #----------------------- 2 -------------------
# # import asyncio

# # # Shared stop signal
# # stop_event = asyncio.Event()

# # async def child_task(name):
# #     while not stop_event.is_set():
# #         print(f"[{name}] working...")
# #         await asyncio.sleep(1)  # simulate work

# #     print(f"[{name}] stopping.")

# # async def intermediate_task(name):
# #     await asyncio.gather(
# #         child_task(f"{name}-child-1"),
# #         child_task(f"{name}-child-2"),
# #     )

# # async def top_level_task():
# #     await asyncio.gather(
# #         intermediate_task("TaskA"),
# #         intermediate_task("TaskB"),
# #     )

# # async def stop_after(delay):
# #     await asyncio.sleep(delay)
# #     stop_event.set()

# # async def main(dev=True):
# #     duration = 10 if dev else float('inf')  # 10 seconds in dev, forever in prod

# #     await asyncio.gather(
# #         top_level_task(),
# #         stop_after(duration)
# #     )

# # asyncio.run(main(dev=True))

# #  #----------------------- 3 -------------------

# import asyncio
# import time

# event = asyncio.Event()

# async def waiter(i):
#     await event.wait()

# async def main():
#     tasks = [asyncio.create_task(waiter(i)) for i in range(10000)]
#     await asyncio.sleep(1)

#     t0 = time.perf_counter()
#     event.set()
#     await asyncio.gather(*tasks)
#     t1 = time.perf_counter()

#     print(f"All done in {t1 - t0:.4f} seconds")

# asyncio.run(main())

{"timestamp": "2025-07-07T21:37:48.306217Z", "service_name": "scraper", "host_id": "elchanans-MacBook-Pro.local", "metric_type": "run_summary", "run_id": "76243103-86b5-4a63-b95d-69848dbd9d0d", "close_status": "planned shutdown", "total_run_duration_ms": 126615.93154200818, "total_exchanges_configured": 1, "fully_successful_exchange_scrapes": 0, "fully_successful_with_errors_exchange_scrapes": 0, "partial_success_exchange_scrapes": 0, "fully_failed_exchange_scrapes": 1, "total_currency_pairs_configured": 60, "successful_currency_pair_initializations": 0, "failed_currency_pair_initializations": 60, "total_data_points_sent_to_redis": 0, "errors_summary": {}, "event": "Monitoring Event", "logger": "scraper.run_summary", "level": "info"}