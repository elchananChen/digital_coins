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
    merge_addition_dicts,
    add_overall_exchange_status
    )


#  monitoring utils
from monitoring.utils import (
    time_async_function,
    handle_async_errors,
    send_metric_log
)

from lists.bit_stamp_lists import bit_stamp_symbols

from monitoring.models import ExchangeScrapeReport, ExchangeCurrencyEvent

# playwright
from playwright._impl._errors import Error as PlaywrightError # Recommended alias

# for errors track

import logging

# redis
from core import send_to_redis_queue

# Configure logging
logger = logging.getLogger(__name__)

async def get_bit_stamp_coin_order_book(bit_stamp_symbol, db_symbol, context,redis_client,exchange_name, event:asyncio.Event,sleep_time=0,run_id=None):
    currency_id=str(uuid.uuid4())
    local_send_to_redis = 0
    local_errors_summary = {}
    page = None
   
    # --- Variables to pass state to finally block ---
    final_status = "failure" # Assume failure until proven otherwise
    
    # variables for ExchangeCurrencyEvent
    initial_latency_ms = None
    latency_avg_ms = 0.0

    try:
        # initial variables
        avg_volume_count = 0
        first_payload_for_channel = True
        last_save_time = None

        # initial page
        page = await context.new_page()

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
                            log_and_categorize_websocket_data_error(
                                e=ValueError("Received empty data payload"),
                                symbol=db_symbol,
                                exchange=exchange_name, 
                                error_summary=local_errors_summary, 
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
                                    error_summary=local_errors_summary,
                                    is_missing_keys_error=True
                                    )
                                return
    
                        data = json_data["data"]
                        origin_asks = data["asks"]
                        origin_bids = data["bids"]
                        origin_time = int(data["timestamp"])
    
                        # Validate that asks and bids have proper structure
                        if not origin_asks and not origin_bids:
                            log_and_categorize_websocket_data_error(e=ValueError("Received empty asks and bids data"),
                                                                    symbol=db_symbol,
                                                                    exchange=exchange_name,
                                                                    error_summary=local_errors_summary,
                                                                    is_validation_error=True
                                                                    )
                            return
    
                        # Convert to datetime in UTC format
                        datetime_utc = datetime.fromtimestamp(origin_time, tz=timezone.utc)
                        timestamp = datetime_utc.isoformat(timespec='milliseconds')
    
                        data =  { "symbol": db_symbol,"exchange": exchange_name,"timestamp": timestamp , "bids": origin_bids,"asks": origin_asks }
                        data_as_string = json.dumps(data)
                        res = await send_to_redis_queue(redis_client, data_as_string, db_symbol,exchange_name,error_summary=local_errors_summary)
    
                        # for monitor
                        if res >= 1:
                            final_status = "success"
                        local_send_to_redis += res # res = 1 / 0
                    except Exception as e:
                        log_and_categorize_websocket_data_error(
                            e=e,
                            symbol=db_symbol,
                            exchange=exchange_name, 
                            error_summary=local_errors_summary,
                            )

                # every time the data come - will be assign to current time
                # for control of the data processing timing without interrupt the frame listening process.
                


                async def on_frame_received(payload: str):
                    nonlocal first_payload_for_channel
                    nonlocal order_books_string 
                    nonlocal last_save_time
                    nonlocal avg_volume_count 
                    nonlocal initial_latency_ms
                    nonlocal latency_avg_ms

                    if last_save_time is None:
                        last_save_time = time.perf_counter()

                    now = time.perf_counter()
                    delay = now - last_save_time
                    if delay >= 1:
                        if f'"channel":"order_book_{bit_stamp_symbol}"' in payload:
                            # return if first payload because it empty
                            if first_payload_for_channel:
                                first_payload_for_channel = False
                                initial_latency_ms = delay * 1000
                                last_save_time = now
                                return

                            order_books_string = payload
                            last_save_time = now

                            # Calculate the latency average
                            current_latency_ms = delay * 1000
                            latency_avg_ms = (latency_avg_ms * avg_volume_count + current_latency_ms) / (avg_volume_count + 1)
                            avg_volume_count += 1

                            # process data
                            asyncio.create_task(process_data())
                ws.on("framereceived", on_frame_received)

        # add the socket listening to the page
        page.on("websocket", on_websocket)
        await asyncio.sleep(sleep_time)

        start_time = time.perf_counter()
        # go to the page and the socket already work in the background
        await page.goto(f"https://www.bitstamp.net/trade/{bit_stamp_symbol}", wait_until="domcontentloaded")
        logger.info(f"🫡 {bit_stamp_symbol} go to page")

        # To run the function always (like while True - just more efficient)
        # stop when in the main.py event.set() will run (stop_task)
        await event.wait()

    except PlaywrightError as e:
        is_page_created = True
        if page is None:
            is_page_created = False
        log_and_categorize_playwright_error(e=e,symbol=db_symbol,error_summary=local_errors_summary,page_created=is_page_created )
        try:
            screenshot_dir = "debug_screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, f"{db_symbol}_playwright_error_{int(time.time())}.png")
            await page.screenshot(path=screenshot_path)
            logger.debug(f"📸 {db_symbol}: Screenshot taken for Playwright error at {screenshot_path}.")
        except PlaywrightError as ss_e:
            await page.close()
            logger.info(f"🔚 Closed page for {bit_stamp_symbol}")
        except Exception as e:
            logger.error(f"❌ Error closing page for {bit_stamp_symbol}: {e}")

    except Exception as e:
        log_general_exception(e=e,symbol=db_symbol, error_summary=local_errors_summary)

    finally:
        if page:
            try:
                await page.close() # Always try to close the page if it was created
                logger.info(f"🔚 Closed page for {bit_stamp_symbol}")
            except Exception as e: # Catch errors specifically during page.close()
                logger.debug(f"❌ Error closing page for {bit_stamp_symbol}: {e}")
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000

        send_metric_log(
            ExchangeCurrencyEvent(
                run_id=run_id,
                component_name=exchange_name,
                event_name="currency_summery",
                currency_pair=db_symbol,
                data_point_id=currency_id,
                initial_latency_ms=initial_latency_ms,
                latency_avg_ms=latency_avg_ms,
                points_send_to_redis=local_send_to_redis,
                duration_ms=duration_ms,
                error_details=local_errors_summary,
                status=final_status,
            )
        )

        return {
            "pair_name": db_symbol,
            "local_send_to_redis":local_send_to_redis,
            "local_errors_summary": local_errors_summary,
            "status": final_status,
        }


@time_async_function(component_name="scraper_run", event_name="exchange_scrape_duration")
@handle_async_errors(component_name="scraper_run", is_critical=True)
async def run_bit_stamp_scraper_redis(context , redis_client,exchange_name,event,delay_per_task,run_id): 
    monitor_data = {
        "total_currency_pairs_configured": len(bit_stamp_symbols),
        "successful_currency_pair_initializations": 0,
        "failed_currency_pair_initializations":0,

        # --- Data Volume and Quality Metrics ---
        "total_data_points_sent_to_redis":0,
        "errors_summary":{}
    }

    tasks = []
    results = []
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
        results = await asyncio.gather(*tasks, return_exceptions=True)
       
    except asyncio.exceptions.CancelledError:
        logger.info("❌ Scraper run was cancelled.")
 

    except Exception as e:
        logger.error(f"🔴 Uncaught critical exception in run_bit_stamp_scraper_redis: {e}")

    finally:
        for res in results:
            # if proper monitor data return and local_send... in it - add it to monitor_data
            if isinstance(res, dict) and "local_send_to_redis" in res:
                monitor_data["total_data_points_sent_to_redis"] += res["local_send_to_redis"]

            if isinstance(res,dict) and "local_errors_summary" in res\
                and isinstance(res["local_errors_summary"],dict):
                merged_data = merge_addition_dicts(res["local_errors_summary"], monitor_data["errors_summary"])
                monitor_data["errors_summary"] = merged_data

            if isinstance(res,dict) and "status" in res:
                # if points send or not to redis for this currency pair
                if res["status"] == "failure":
                    monitor_data["failed_currency_pair_initializations"] += 1
                    logger.info(f"🔴 no points send to redis for: {res['pair_name']}")
                elif res["status"] == "success":
                    monitor_data["successful_currency_pair_initializations"] += 1

            elif isinstance(res, Exception): # This means an exception escaped get_bit_stamp_coin_order_book entirely
                monitor_data["failed_currency_pair_initializations"] += 1
                logger.error(f"🔴 Critical exception escaped task for a scraper: {type(res).__name__}: {res}")
                # You can log this specific exception to the general_scraper_exception in errors_summary
                log_general_exception(e=res, symbol="GLOBAL_SCRAPER_RUN", error_summary=monitor_data["errors_summary"])

        add_overall_exchange_status(monitor_data)

        return ExchangeScrapeReport(
           run_id=run_id,
           exchange_name=exchange_name,
           overall_exchange_status=monitor_data["status"],
           total_currency_pairs_configured=monitor_data["total_currency_pairs_configured"],
           successful_currency_pair_initializations=monitor_data["successful_currency_pair_initializations"],
           failed_currency_pair_initializations=monitor_data["failed_currency_pair_initializations"],
           total_data_points_sent_to_redis=monitor_data["total_data_points_sent_to_redis"],
           errors_summary=monitor_data["errors_summary"]
        )