# dates
from datetime import datetime, timezone
from time import time

import json

# for async 
import asyncio

# functions from the project
from core.models import OrderBook
from utils.scraping_utils import wait_for_elements
from lists.bit_stamp_lists import bit_stamp_symbols
from playwright._impl._errors import TargetClosedError

# for errors track
import traceback
import logging

# redis 
from core import send_to_redis_queue


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


insert_tracker = {"start": datetime.now(), "coins_sum": len(bit_stamp_symbols)}
errors_tracker = {}
relevant_payloads_tracker_with_timeout = {}
relevant_payloads_tracker = {}
save_to_db_time_tracker = {}


def update_tracker(tracker: dict, symbol: str, first_message = None, error_type: None | str = None, insert_time:None | int = None):
    if symbol not in tracker:
        if insert_time:
            tracker[symbol]= [insert_time]
        if first_message:
            print(first_message)
        if error_type:
            tracker[symbol] = {error_type: 1}
            return
        tracker[symbol] = [1, str(datetime.now())]
    else:
        if insert_time:
            tracker[symbol].append(insert_time)
        if error_type:
            tracker[symbol][error_type] +=1
            return
        tracker[symbol][0] += 1


async def get_bit_stamp_coin_order_book(bit_stamp_symbol, db_symbol, context,redis_client, sleep_time=0):
    try:
        page = await context.new_page()

        #   socket definition
        def on_websocket(ws):
                # for catching the payload
                # will be overwrite every half a second 
                order_books_string = ""

                async def process_data():
                    nonlocal order_books_string
                    # print(f"Processing {len(order_books_string)} items")

                    # Convert to json
                    json_data = json.loads(order_books_string)
    
                    # TODO: add here full validation of the data
                    if "data" not in json_data:
                        print("no data in json")
                        traceback.print_exc()
                        update_tracker(errors_tracker, db_symbol, error_type=f"no_data")
                        return
                    # print(json_data["data"])
                    json_data_keys = ["asks","bids", "timestamp"]
                    for key in json_data_keys:
                        if key  not in json_data["data"]:
                            logger.error(f"❗️no {key} in json for bit_stamp {db_symbol}")
                            update_tracker(errors_tracker, db_symbol, error_type=f"no_{key}")
                            return

                    data = json_data["data"]
                    origin_asks = data["asks"]
                    origin_bids = data["bids"]
                    origin_time = int(data["timestamp"])

                    # Validate that asks and bids have proper structure
                    if not origin_asks and not origin_bids:
                        logger.warning(f"⚠️ {db_symbol}: Both asks and bids are empty")

                    # Convert to datetime in UTC format
                    datetime_utc = datetime.fromtimestamp(origin_time, tz=timezone.utc)
                    timestamp = datetime_utc.isoformat(timespec='milliseconds')

                    data =  { "symbol": db_symbol,"exchange": "bitStamp","timestamp": timestamp , "bids": origin_bids,"asks": origin_asks }
                    data_as_string = json.dumps(data)
                    send_to_redis_queue(redis_client, data_as_string)
    
                # every time the data come - will be assign to this time
                # for control of the data processing timing without interrupt the frame listening process.
                last_save_time = 0
                async def on_frame_received(payload: str):
                    nonlocal order_books_string 
                    nonlocal last_save_time 
                    now = time()
                    if f'"channel":"order_book_{bit_stamp_symbol}"' in payload:
                            update_tracker(relevant_payloads_tracker,db_symbol)
                    if now - last_save_time >= 1:  
                        if f'"channel":"order_book_{bit_stamp_symbol}"' in payload:
                            update_tracker(relevant_payloads_tracker_with_timeout,db_symbol)
                            order_books_string = payload
                            last_save_time = now
                            asyncio.create_task(process_data())
                ws.on("framereceived", on_frame_received)
    
        # add the socket listening to the page
        page.on("websocket", on_websocket)
        await asyncio.sleep(sleep_time)
        # print(f"{db_symbol} initial")
        # go to the page and the socket already work in the background
        await page.goto(f"https://www.bitstamp.net/trade/{bit_stamp_symbol}", wait_until="domcontentloaded")
    
        # To run the function always (like while True - just more efficient)
        await asyncio.Event().wait() 
    except Exception as e:
        logger.error(f"❌ {bit_stamp_symbol}: Error in main function: {e}")
        update_tracker(errors_tracker, db_symbol, error_type=f"unknown_in_get_bit_stamp_coin_order_book")
        traceback.print_exc()    
    finally:
        if page:
            try:
                await page.close()
                logger.info(f"🔚 Closed page for {bit_stamp_symbol}")
            except Exception as e:
                logger.error(f"❌ Error closing page for {bit_stamp_symbol}: {e}")


async def safe_wrapper(coro):
    global insert_tracker
    try:
        await coro
    except TargetClosedError as e:
        print(f"[TargetClosedError Browser or page closed unexpectedly: {e}")
    except Exception as e:
        logger.warning(f"error {e}")
        
# all coins running together in the same time
#  but! initial the process after some time for each batch
async def run_bit_stamp_scraper(context , redis_client):
    tasks = []
    print(f"Total symbols: {len(bit_stamp_symbols)}")
    initial_delay = 10
    for i, (db_symbol,bit_stamp_symbol) in enumerate(bit_stamp_symbols.items()):
        if initial_delay == i:
            initial_delay += 10
        sleep_time = initial_delay -10
        task = asyncio.create_task(safe_wrapper(get_bit_stamp_coin_order_book(bit_stamp_symbol, db_symbol, context, redis_client, sleep_time )))
        tasks.append(task)
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        end = datetime.now()
        total_time = end - insert_tracker["start"] 
        insert_tracker.update({
            "end": datetime.now(),
            "total_time": str(total_time)
        })

        print(f"sum of the coins insert successfully is {len(insert_tracker) - 4}")
        print("errors_tracker", errors_tracker)
        print("relevant_payloads_tracker ",relevant_payloads_tracker)
        print("relevant_payloads_tracker_timeout ",relevant_payloads_tracker_with_timeout)
        print("save_to_db_time_tracker ",save_to_db_time_tracker)
        print("relevant_payloads_tracker_timeout ",relevant_payloads_tracker_with_timeout)
        print("insert_tracker: ", insert_tracker)

    except Exception as e:
        print("🔴 Uncaught exception in tasks:", e)


