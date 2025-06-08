# https://www.bybit.com/en/trade/spot/BTC/USDT

# dates
from datetime import datetime, timezone

# for async 
import asyncio

# for errors track
import traceback
from webbrowser import get

from core.models import OrderBook
from time import sleep

 
from utils.scraping_utils import wait_for_elements

import queue
import time
import json
# !!  canvas !


by_bit_symbols = {
    "BTCUSDT":"BTC/USDT", 
    "ETHUSDT":"ETH/USDT", 
    "LTCUSDT":"LTC/USDT", 
    "XRPUSDT":"XRP/USDT", 
    "BCHUSDT":"BCH/USDT", 
}


async def save_to_db(data, exchange_name, exchange_symbol):
    try:           
        price_doc = OrderBook(**data)
        await price_doc.insert()
        print(f"Inserted {exchange_name} {exchange_symbol} at {data['timestamp']}")
    except Exception as e:
        print(f"Error fetching data: {e}")
        traceback.print_exc()

async def get_by_bit_coin_order_book(by_bit_symbol, db_symbol, context):
    page = await context.new_page()
        
    def on_websocket(ws):
            # will be overwrite every half a second
            order_books_string = ""

            async def process_data():
                nonlocal order_books_string
                # print(f"Processing {len(order_books_string)} items")

                # Convert to json
                json_data = json.loads(order_books_string)

                # TODO: add here full validation of the data
                if "topic" not in json_data:
                    print("no topic in json")
                    traceback.print_exc()
                    return
                
                origin_asks = json_data["data"][0]["a"]
                origin_bids = json_data["data"][0]["b"]
                origin_time = json_data["data"][0]["t"]
            
                # Convert to datetime in UTC format
                timestamp_s = origin_time / 1000
                datetime_utc = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
                timestamp = datetime_utc.isoformat(timespec='milliseconds')
                
                asks = []
                bids = []
                for ask in origin_asks:
                    asks.append({"price": ask[0] , "amount": ask[1]} )
                for bid in origin_bids:
                    bids.append({"price": bid[0] , "amount": bid[1]} )
                data =  { "symbol": db_symbol,"exchange": "byBit","timestamp": timestamp , "bids": bids,"asks": asks }
                # print (data)
                await save_to_db(exchange_name="by_bit", data=data, exchange_symbol=by_bit_symbol)
               

            # every time the data come - will be assign to this time
            # for control of the data processing timing without interrupt the frame listening process.
            last_save_time = 0
        
            async def on_frame_received(payload: str):
                nonlocal order_books_string 
                nonlocal last_save_time 
                
                now = time.time()

                if now - last_save_time >= 1:  
                    if '"topic":"mergedDepth"' in payload:
                        order_books_string = payload
                        last_save_time = now
                        asyncio.create_task(process_data())
            ws.on("framereceived", on_frame_received)

    page.on("websocket", on_websocket)

    await page.goto(f"https://www.bybit.com/en/trade/spot/{by_bit_symbol}", wait_until="domcontentloaded")
   
    # To run the function always (like while True - just more efficient)
    await asyncio.Event().wait() 




async def run_by_bit_scraper(context):
    tasks = [] 
    for db_symbol,by_bit_symbol in by_bit_symbols.items():
        task = asyncio.create_task(get_by_bit_coin_order_book(by_bit_symbol, db_symbol, context))
        tasks.append(task)
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        print("🔴 Uncaught exception in tasks:", e)
