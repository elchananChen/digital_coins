import time
import json
import uuid
import asyncio
import logging
import os

# dates
from datetime import datetime, timezone

from utils import log_general_exception
from utils.error_handlers import log_and_categorize_websocket_data_error ,log_and_categorize_playwright_error
from utils.util_functions import merge_addition_dicts ,add_overall_exchange_status
from monitoring.utils import send_metric_log,time_async_function
from monitoring.models import ExchangeCurrencyEvent,ExchangeScrapeReport
from core.redis import send_to_redis_queue


# playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError  

from lists.by_bit_lists import by_bit_symbols

logger = logging.getLogger(__name__)

# by_bit_symbols = {
#     "BTCUSDT":"BTC/USDT", 
#     "ETHUSDT":"ETH/USDT", 
#     "LTCUSDT":"LTC/USDT", 
#     "XRPUSDT":"XRP/USDT", 
#     "BCHUSDT":"BCH/USDT", 
# }


async def get_by_bit_coin_order_book(by_bit_symbol, db_symbol, context,exchange_name:str,redis_client,event:asyncio.Event,sleep_time=0,run_id=None):
    currency_id=str(uuid.uuid4())
    local_send_to_redis = 0
    local_errors_summary = {}
    final_status = "failure" 
    page = None

    # for ExchangeCurrencyEvent
    initial_latency_ms = None
    latency_avg_ms = 0.0
    
     #  for retry logic
    MAX_RETRIES = 3  
    RETRY_DELAY_SEC = 10

    for attempt in range(MAX_RETRIES):
        try:
             # initial variables
            avg_volume_count = 0
            first_payload_for_channel = True
            last_save_time = None
            start_time = time.perf_counter()
    
            # initial page
            page = await context.new_page()
            def on_websocket(ws):
                    logger.info("on websocket")
                     # for catching the payload
                    # will be overwrite every half a second
                    order_books_string = ""

                    async def process_data():
                        logger.info("process data")
                        try:
                            nonlocal final_status
                            nonlocal order_books_string
                            nonlocal local_errors_summary
                            # print(f"Processing {len(order_books_string)} items")
        
                            # Convert to json
                            json_data = json.loads(order_books_string)
        
                            if "data" not in json_data or not isinstance("data",list):
                                log_and_categorize_websocket_data_error(
                                    e=ValueError("Received empty data payload"),
                                    symbol=db_symbol,
                                    exchange=exchange_name, 
                                    error_summary=local_errors_summary, 
                                    is_empty_data_error=True
                                    )
                                return
        
                            json_data_keys = ["a","b", "t"]
                            for key in json_data_keys:
                                if key  not in json_data["data"][0]:
                                    log_and_categorize_websocket_data_error(
                                        e=KeyError("Missing keys in payload data"),
                                        symbol=db_symbol,
                                        exchange=exchange_name,
                                        error_summary=local_errors_summary,
                                        is_missing_keys_error=True
                                        )
                                    return
        
                            origin_asks = json_data["data"][0]["a"]
                            origin_bids = json_data["data"][0]["b"]
                            origin_time = json_data["data"][0]["t"]
        
                            # Convert to datetime in UTC format
                            timestamp_s = origin_time / 1000
                            datetime_utc = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
                            timestamp = datetime_utc.isoformat(timespec='milliseconds')
        
                            # Validate that asks and bids have proper structure
                            if not origin_asks and not origin_bids:
                                log_and_categorize_websocket_data_error(
                                    e=ValueError("Received empty asks and bids data"),
                                    symbol=db_symbol,
                                    exchange=exchange_name,
                                    error_summary=local_errors_summary,
                                    is_validation_error=True
                                    )
                                return
        
                            data =  {
                                "symbol": db_symbol,
                                "exchange": exchange_name,
                                "timestamp": timestamp ,
                                "bids": origin_bids,
                                "asks": origin_asks 
                                }
        
                            data_as_string = json.dumps(data)
                            res = await send_to_redis_queue(
                                redis_client, 
                                data_as_string, 
                                db_symbol,
                                exchange_name,
                                error_summary=local_errors_summary
                                )
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
        
                    # every time the data come - will be assign to this time
                    # for control of the data processing timing without interrupt the frame listening process.
                    last_save_time = 0
                
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

                        if delay >= 0.5:
                            if '"topic":"mergedDepth"' in payload:
                                print(payload)
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

            page.on("websocket", on_websocket)
            await asyncio.sleep(sleep_time)

            start_time = time.perf_counter()

            await page.goto(f"https://www.bybit.com/en/trade/spot/{by_bit_symbol}", wait_until="domcontentloaded")
            logger.info(f"🫡 {db_symbol}@{exchange_name} go to page")
    
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
                error_summary=local_errors_summary,
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
                continue  # Go to the next loop attempt
            else:
                # All attempts failed – mark as a final failure and return
                logger.error(f"❌ {db_symbol}: All {MAX_RETRIES} attempts to navigate failed due to timeout.")
                final_status = "failure"  # Ensure failure status is set
                return {
                    "pair_name": db_symbol,
                    "local_send_to_redis": local_send_to_redis,
                    "local_errors_summary": local_errors_summary,
                    "status": final_status,
                }
        
        except PlaywrightError as e:
            is_page_created = True
            if page is None:
                is_page_created = False
            log_and_categorize_playwright_error(
                e=e,
                symbol=db_symbol,
                error_summary=local_errors_summary,
                page_created=is_page_created 
                )
            try:
                screenshot_dir = "debug_screenshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshot_dir, f"{db_symbol}_playwright_error_{int(time.time())}.png")
                await page.screenshot(path=screenshot_path)
                logger.info(f"📸 {db_symbol}: Screenshot taken for Playwright error at {screenshot_path}.")
                break
            except PlaywrightError as ss_e:
                await page.close()
                logger.info(f"🔚 Closed page for {db_symbol}@{exchange_name}")
                break
            except Exception as e:
                logger.error(f"❌ Error closing page for {db_symbol}@{exchange_name}: {e}")
                break
    
        except Exception as e:
            log_general_exception(e=e,symbol=db_symbol, error_summary=local_errors_summary)
            break

        finally:
            if page:
                try:
                    await page.close() 
                    logger.info(f"🔚 Closed page for {db_symbol}@{exchange_name}")
                except Exception as e: 
                    logger.error(f"❌ Error closing page for {db_symbol}@{exchange_name}: {e}")
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
async def run_by_bit_scraper(context , redis_client,exchange_name,event,delay_per_task,run_id):
    monitor_data = {
    "total_currency_pairs_configured": len(by_bit_symbols),
    "successful_currency_pair_initializations": 0,
    "failed_currency_pair_initializations":0,
    # --- Data Volume and Quality Metrics ---
    "total_data_points_sent_to_redis":0,
    "errors_summary":{}
    }

    tasks = [] 
    results = []
    logger.info(f"Total symbols: {len(by_bit_symbols)}")

    for i ,(db_symbol,by_bit_symbol) in enumerate(by_bit_symbols.items()):
        sleep_time = i * delay_per_task
        task = asyncio.create_task(
            get_by_bit_coin_order_book(
                by_bit_symbol=by_bit_symbol,
                db_symbol=db_symbol,
                context=context,
                redis_client=redis_client,
                exchange_name=exchange_name,
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
        logger.error(f"🔴 Uncaught critical exception in run_by_bit_scraper: {e}")
    
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
