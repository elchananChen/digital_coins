
# dates
from datetime import datetime, timezone
import time 

# python
import json 
import asyncio
import os
import uuid
# utils functions
from utils import (
    log_and_categorize_playwright_error,
    log_general_exception,
    log_and_categorize_websocket_data_error,
    )


#  monitoring utils
from monitoring.utils import (
    time_async_function,
    get_or_create_currency_metrics,
    update_latency_avg
)

from lists.bit_stamp_lists import bit_stamp_symbols

from monitoring.models import ExchangeCurrencyEvent

# playwright
from patchright._impl._errors import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError  

# for errors track

import logging

# redis
from core import send_to_redis_queue

from monitoring.global_metric_dicts import EXCHANGES_METRICS

CURRENT_EXCHANGE_METRICS = EXCHANGES_METRICS["bitStamp"]


# Configure logging
logger = logging.getLogger(__name__)

async def get_bit_stamp_coin_order_book(bit_stamp_symbol, db_symbol, context,redis_client,exchange_name, event:asyncio.Event,sleep_time=0,run_id=None):
    currency_id=str(uuid.uuid4())
    local_send_to_redis = 0
    final_status = "failure" # Assume failure until proven otherwise
    page = None

    # for ExchangeCurrencyEvent
    latency_avg_ms = 0.0

    CURRENT_CURRENCY_METRICS = get_or_create_currency_metrics(
        db_symbol=db_symbol,
        exchange_metrics=CURRENT_EXCHANGE_METRICS, 
        currency_id=currency_id
        )

    #  for retry logic
    MAX_RETRIES = 10  
    RETRY_DELAY_SEC = 10

    for attempt in range(MAX_RETRIES):
        try:
            # initial variables
            avg_volume_count = 0
            first_payload_for_channel = True

            # initial page
            page = await context.new_page()
    
            # socket definition
            def on_websocket(ws):
                    logger.info(f"{db_symbol} {exchange_name}on websocket")
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
                                log_and_categorize_websocket_data_error(
                                    e=ValueError("Received empty data payload"),
                                    symbol=db_symbol,
                                    exchange=exchange_name, 
                                    error_summary=CURRENT_CURRENCY_METRICS["error_details"], 
                                    is_empty_data_error=True
                                    )
                                return
                            
                            # logger.info(json_data["data"])
                            json_data_keys = ["asks","bids", "timestamp"]
                            for key in json_data_keys:
                                if key  not in json_data["data"]:
                                    log_and_categorize_websocket_data_error(
                                        e=KeyError("Missing keys in payload data"),
                                        symbol=db_symbol,
                                        exchange=exchange_name,
                                        error_summary=CURRENT_CURRENCY_METRICS["error_details"],
                                        is_missing_keys_error=True
                                        )
                                    return
        
                            data = json_data["data"]
                            origin_asks = data["asks"]
                            origin_bids = data["bids"]
                            origin_time = int(data["timestamp"])
        
                            # Validate that asks and bids have proper structure
                            if not origin_asks and not origin_bids:
                                log_and_categorize_websocket_data_error(
                                    e=ValueError("Received empty asks and bids data"),
                                    symbol=db_symbol,
                                    exchange=exchange_name,
                                    error_summary=CURRENT_CURRENCY_METRICS["error_details"],
                                    is_validation_error=True
                                    )
                                return
        
                            # Convert to datetime in UTC format
                            datetime_utc = datetime.fromtimestamp(origin_time, tz=timezone.utc)
                            timestamp = datetime_utc.isoformat(timespec='milliseconds')
        
                            data =  { "symbol": db_symbol,"exchange": exchange_name,"timestamp": timestamp , "bids": origin_bids,"asks": origin_asks }
                            data_as_string = json.dumps(data)
                            res = await send_to_redis_queue(
                                redis_client, 
                                data_as_string, 
                                db_symbol,
                                exchange_name,
                                error_summary=CURRENT_CURRENCY_METRICS["error_details"]
                                )

                            # for monitor
                            if res >= 1: 
                                final_status = "success" 

                            CURRENT_CURRENCY_METRICS["points_send_to_redis"] += res # res = 1 / 0
                        except Exception as e:
                            log_and_categorize_websocket_data_error(
                                e=e,
                                symbol=db_symbol,
                                exchange=exchange_name, 
                                error_summary=CURRENT_CURRENCY_METRICS["error_details"],
                                )

                    # every time the data come - will be assign to current time
                    # for control of the data processing timing without interrupt the frame listening process.
                    last_save_time = time.perf_counter()

                    async def on_frame_received(payload: str):
                        nonlocal first_payload_for_channel
                        nonlocal order_books_string 
                        nonlocal last_save_time
                        nonlocal avg_volume_count 
                        nonlocal latency_avg_ms
    
                        if last_save_time is None:
                            last_save_time = time.perf_counter()
    
                        now = time.perf_counter()
                        delay = now - last_save_time
                        if delay >= 0.5:
                            if f'"channel":"order_book_{bit_stamp_symbol}"' in payload:
                                # return if first payload because it empty
                                if first_payload_for_channel:
                                    first_payload_for_channel = False
                                    CURRENT_CURRENCY_METRICS["initial_latency_ms"] = delay * 1000
                                    last_save_time = now
                                    return

                                order_books_string = payload
                                last_save_time = now
    
                                # update latency average
                                current_latency_ms = delay * 1000
                                update_latency_avg(
                                    metrics=CURRENT_CURRENCY_METRICS,
                                    current_latency_ms=current_latency_ms
                                    )
                                
                                # process data
                                asyncio.create_task(process_data())
                    ws.on("framereceived", on_frame_received)
    
            # add the socket listening to the page
            page.on("websocket", on_websocket)
            await asyncio.sleep(sleep_time)
            print(CURRENT_EXCHANGE_METRICS["currency_pair_initialized"])
            CURRENT_EXCHANGE_METRICS["currency_pair_initialized"] += 1

            # go to the page and the socket already work in the background
            await page.goto(f"https://www.bitstamp.net/trade/{bit_stamp_symbol}", wait_until="domcontentloaded",timeout=100000)
            logger.info(f"{db_symbol}@{exchange_name} go to page")

            # To run the function always (like while True - just more efficient)
            # stop when in the main.py event.set() will run (stop_task)
            await event.wait()
            break

        except PlaywrightTimeoutError as e:
            # Make sure you've imported this: from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError
            logger.warning(f"⚠️ {db_symbol}@{exchange_name}: Navigation Timeout on attempt {attempt + 1}/{MAX_RETRIES}: {e}")
        
            # log and categorize the error
            is_page_created = True
            if page is None:
                is_page_created = False

            log_and_categorize_playwright_error(
                e=e,
                symbol=db_symbol,
                error_summary=CURRENT_CURRENCY_METRICS["error_details"],
                page_created=is_page_created
                )

            if page:
                # Try to close the page if it was created (to prevent resource leaks)
                try:
                    await page.close()
                    logger.info(f"🔚 Closed timed-out page for {db_symbol}@{exchange_name}")
                except Exception as close_e:
                    logger.error(f"❌ Error closing timed-out page for {db_symbol}@{exchange_name}: {close_e}")
        
                # Reset the page so a new one is created on the next attempt
                page = None
            if attempt < MAX_RETRIES - 1:
                # Wait before retrying
                await asyncio.sleep(RETRY_DELAY_SEC)
                continue
            else:
                # All attempts failed – mark as a final failure and return
                logger.error(f"❌ {db_symbol}: All {MAX_RETRIES} attempts to navigate failed due to timeout.")
                final_status = "failure"
                continue

        except PlaywrightError as e:
            is_page_created = True
            if page is None:
                is_page_created = False
            log_and_categorize_playwright_error(
                e=e,
                symbol=db_symbol,
                error_summary=CURRENT_CURRENCY_METRICS["error_details"],
                page_created=is_page_created 
                )
            try:
                screenshot_dir = "debug_screenshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshot_dir, f"{db_symbol}_playwright_error_{int(time.time())}.png")
                await page.screenshot(path=screenshot_path)
                logger.info(f"📸 {db_symbol}: Screenshot taken for Playwright error at {screenshot_path}.")
                await asyncio.sleep(RETRY_DELAY_SEC)
                continue
            except PlaywrightError as ss_e:
                await page.close()
                logger.info(f"🔚 Closed page for {db_symbol}@{exchange_name}")
                await asyncio.sleep(RETRY_DELAY_SEC)
                continue
            except Exception as e:
                logger.error(f"❌ Error closing page for {db_symbol}@{exchange_name}: {e}")
                await asyncio.sleep(RETRY_DELAY_SEC)
                continue
    
        except Exception as e:
            logger.error("Exception")
            logger.error(f"Type of error caught: {type(e)}")
            logger.error(f"Error message: {e}")
            log_general_exception(e=e,symbol=db_symbol, error_summary=CURRENT_CURRENCY_METRICS["error_details"])
            await asyncio.sleep(RETRY_DELAY_SEC)
            continue
    
        finally:
            if page:
                try:
                    await page.close() 
                    logger.info(f"🔚 Closed page for {bit_stamp_symbol}")
                except Exception as e: 
                    logger.error(f"❌ Error closing page for {bit_stamp_symbol}: {e}")

# @handle_async_errors(component_name="scraper_run", is_critical=True)
@time_async_function(component_name="scraper_run", event_name="exchange_scrape_duration")
async def run_bit_stamp_scraper(context , redis_client,exchange_name,event,delay_per_task,run_id): 

    tasks = []
    logger.info(f"Total symbols: {len(bit_stamp_symbols)}")

    # all coins running together in the same time
    #  but! initial the process after some time for each batch
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
                sleep_time=sleep_time,
                run_id=run_id
                  ))
        tasks.append(task)
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
       
    except asyncio.exceptions.CancelledError:
        logger.info("❌ Scraper run was cancelled.")
 
    except Exception as e:
        logger.error(f"🔴 Uncaught critical exception in run_bit_stamp_scraper: {e}")