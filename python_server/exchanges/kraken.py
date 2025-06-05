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
kraken_symbols = {
    "BTCUSD":"btc-usd", 
    "ETHUSD":"eth-usd", 
    "LTCUSD":"ltc-usd", 
    "XRPUSD":"xrp-usd", 
    "BCHUSD":"bch-usd", 
}

async def fetch_kraken_data(page,db_symbol):    
    #  ! get the order book wrapper 
    wrapper = page.locator("//div[@class='flex-1 flex relative overflow-auto h-full']//div[@class='size-full flex flex-col']//div[@class='flex size-full relative overflow-hidden justify-center flex-col']//div[contains(@class, 'group relative divide-y divide-transparent w-full')]")

    # ! get the ask and bids wrapper
    asks_wrapper = wrapper.nth(0)
    bids_wrapper = wrapper.nth(1)

    # ! get the rows asks and bids container
    rows_asks = asks_wrapper.locator("//div[@class='flex items-center relative h-6']")
    rows_bids = bids_wrapper.locator("//div[@class='flex items-center relative h-6']")
    
    # ! run on the "asks and bids rows"
    # ! get the price and amount for every row + append them to "asks" and "bids"
    try:
        count = await rows_asks.count()
        now = datetime.now(timezone.utc)
        asks = []
        bids = []
        for i in range(count):
            row_asks = rows_asks.nth(i)
            row_bids = rows_bids.nth(i)

            ask_price = await row_asks.locator("//span[contains(@class, 'hover:font-bold')]").nth(0).inner_text()
            ask_amount = await row_asks.locator("//span[contains(@class, 'hover:font-bold')]").nth(1).inner_text()
            
            bid_price = await row_bids.locator("//span[contains(@class, 'hover:font-bold')]").nth(0).inner_text()
            bid_amount = await row_bids.locator("//span[contains(@class, 'hover:font-bold')]").nth(1).inner_text()

            ask =  {"price": ask_price.replace(',', ''),"amount": ask_amount.replace(',', '')}
            bid =  {"price": bid_price.replace(',', ''),"amount": bid_amount.replace(',', '')}
            asks.append(ask)
            bids.append(bid)

        # ! make a valid db data for kraken
        data =  { "symbol": db_symbol,"exchange": "kraken","timestamp": now , "bids": bids,"asks": asks }

        # ! check that the highest bid low from the lower ask
        try:    
            assert float(asks[count - 1]["price"]) > float(bids[0]["price"]), "❌ ask price should be greater than bid price"
            print("✅ Logical order book structure verified.")
        except AssertionError as e:
            print(str(e))  

        # !return data
        # print(data)
        return data

    except TimeoutError:
        print("❌ Element did not appear in time – maybe the page is slow or the XPath is incorrect")
        traceback.print_exc()
    except Exception as e:
        print(f"❗ Unexpected error: {e}")


async def get_kraken_coin_order_book(kraken_symbol,db_symbol, context):
    page = await context.new_page()
    await page.goto(f"https://pro.kraken.com/app/trade/{kraken_symbol}", wait_until="domcontentloaded")
    
    # ! wait for the first ask to load and wait one more second
    await asyncio.sleep(5)
    sk_light_object =page.locator("css=div.group")
    await wait_for_elements(sk_light_object,1)
    print("get ask_light_object")
    await asyncio.sleep(5)

     # ! run every second and update data without navigation
    while True:
            try:
                data = await fetch_kraken_data(page, db_symbol)
                if data:
                    price_doc = OrderBook(**data)
                    await price_doc.insert()
                    print(f"Inserted kraken {kraken_symbol} at {data['timestamp']}")
            except Exception as e:
                print(f"Error fetching data: {e}")
                traceback.print_exc()
            await asyncio.sleep(1) 




async def run_kraken_scraper(context):
    tasks = [] 
    for db_symbol,kraken_symbol in kraken_symbols.items():
        task = asyncio.create_task(get_kraken_coin_order_book(kraken_symbol, db_symbol, context))
        tasks.append(task)
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        print("🔴 Uncaught exception in tasks:", e)
