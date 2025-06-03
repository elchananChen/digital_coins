import asyncio
import traceback
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document 
from pymongo import IndexModel, ASCENDING, DESCENDING
from playwright.async_api import async_playwright
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List
import os
import psutil
import threading

# environment variables
load_dotenv()  

DB_URI = os.getenv("DB_URI")
DB_NAME = os.getenv("DB_NAME", "digitalCoins")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ScrapingOrderBook")

# DB types classes
class Order(BaseModel):
    price: str
    amount: str

class OrderBook(Document):
    symbol: str
    exchange: str
    timestamp: datetime
    bids: List[Order] 
    asks: List[Order]
    class Settings:
        name = COLLECTION_NAME
        indexes = [
            IndexModel(
                [("timestamp", ASCENDING)],
                expireAfterSeconds=600  
            ),
            IndexModel([("symbol", ASCENDING),("exchange",ASCENDING), ("timestamp", DESCENDING)])
        ]    

binance_symbols = {
    "BTCUSDT":"BTC_USDT", 
    "ETHUSDT":"ETH_USDT", 
    "LTCUSDT":"LTC_USDT", 
    "XRPUSDT":"XRP_USDT", 
    "BCHUSDT":"BCH_USDT", 
}

# monitor
def monitor_resource_usage(interval=2):
    process = psutil.Process(os.getpid())
    while True:
        cpu_percent = process.cpu_percent(interval=interval)
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / (1024 ** 2)
        print(f"📊 [Monitor] CPU: {cpu_percent:.2f}% | RAM: {mem_mb:.2f} MB")

def start_monitoring():
    t = threading.Thread(target=monitor_resource_usage, daemon=True)
    t.start()


# binance 
async def get_binance_coin_order_book(binance_symbol,db_symbol, browser):
    page = await browser.new_page()
    await page.goto(f"https://www.binance.com/en/trade/{binance_symbol}?_from=markets&type=spot", wait_until="domcontentloaded")
    
    # wait for the first ask to load and wait one more second
    ask_light_object = page.locator("css=div.ask-light")
    await ask_light_object.first.wait_for(timeout=20000)
    await asyncio.sleep(0.5)
    
    # run every second and update data without navigation
    while True:
            try:
                data = await fetch_binance_data(page, db_symbol)
                if data:
                    price_doc = OrderBook(**data)
                    await price_doc.insert()
                    print(f"Inserted binance {binance_symbol} at {data['timestamp']}")
            except Exception as e:
                print(f"Error fetching data: {e}")
                traceback.print_exc()
            await asyncio.sleep(1) 

#  wait for elements to start the app without errors
async def wait_for_elements(locator, count, timeout=10000, poll_interval=200):
    # Wait until locator finds at least `count` elements
    elapsed = 0

    while elapsed < timeout:
        elements_found = await locator.count()
        if elements_found >= count:
            return True
        await asyncio.sleep(poll_interval / 1000)
        elapsed += poll_interval

    # Raise error if not enough elements found in time
    raise TimeoutError(f"Expected at least {count} elements, but found {elements_found} after {timeout}ms.")

#  
async def fetch_binance_data(page,db_symbol):
        try:
            rows_asks = page.locator("//div[@class='orderbook-list orderbook-bid has-overlay']//div[contains(@class, 'row-content')]")
            rows_bids = page.locator("//div[@class='orderbook-list orderbook-ask has-overlay']//div[contains(@class, 'row-content')]")
            count = await rows_asks.count()
            now = datetime.now(timezone.utc)
            asks = []
            bids = []
            for i in range(count):
                row_asks = rows_asks.nth(i)
                row_bids = rows_bids.nth(i)

              
                ask_price = await row_asks.locator("div").nth(0).inner_text()
                ask_amount = await row_asks.locator("div").nth(1).inner_text()
            
                bid_price = await row_bids.locator("div").nth(0).inner_text()
                bid_amount = await row_bids.locator("div").nth(1).inner_text()
            
                ask =  {"price": ask_price.replace(',', ''),"amount": ask_amount.replace(',', '')}
                bid =  {"price": bid_price.replace(',', ''),"amount": bid_amount.replace(',', '')}

                asks.append(ask)
                bids.append(bid)
 

            data = { "symbol": db_symbol,"exchange": "binance", "timestamp":now, "bids": bids,"asks": asks }
            return data
        except TimeoutError:
            print("❌ Element did not appear in time – maybe the page is slow or the XPath is incorrect")
        except Exception as e:
            print(f"❗ Unexpected error: {e}")



async def main():
    #  start_monitoring()
     client = AsyncIOMotorClient(DB_URI)
     await init_beanie(database=client[DB_NAME], document_models=[OrderBook])
     
     async with async_playwright() as p:
        
        # open browser and go to binance bitcoin
        browser = await p.chromium.launch(headless=True) 
        tasks = [] 
        for db_symbol,binance_symbol in binance_symbols.items():
            task = asyncio.create_task(get_binance_coin_order_book(binance_symbol, db_symbol, browser))
            tasks.append(task)
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            print("🔴 Uncaught exception in tasks:", e)

asyncio.run(main())
