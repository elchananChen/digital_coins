# dates
from datetime import datetime, timezone

# for async 
import asyncio

# for errors track
import traceback

from core.models import OrderBook
from time import sleep


from utils.scraping_utils import wait_for_elements
kraken_symbols = {
    "BTCUSD":"btc-usd", 
    # "ETHUSD":"eth-usd", 
    # "LTCUSD":"ltc-usd", 
    # "XRPUSD":"xrp-usd", 
    # "BCHUSD":"bch-usd", 
}

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
            traceback.print_exc()
        except Exception as e:
            print(f"❗ Unexpected error: {e}")


async def get_kraken_coin_order_book(kraken_symbol,db_symbol, browser):
    page = await browser.new_page()
    await page.goto(f"https://pro.kraken.com/app/trade/{kraken_symbol}", wait_until="domcontentloaded")
    
    # wait for the first ask to load and wait one more second
    sleep(5)
    sk_light_object =page.locator("css=div.group")
    # print(title)
    print("get ask_light_object")
    await wait_for_elements(sk_light_object,1)


    ask_light_object =page.locator("css=div.group div")

    if await ask_light_object.count() == 0:
        print("ask_light_object not exist")
    else: 
        print("ask_light_object exist")    
    
    # await ask_light_object.first.wait_for(timeout=20000)
    await asyncio.sleep(1)

    # print(f"ask_light_object: {ask_light_object}")
    print(ask_light_object)
    texts = await ask_light_object.all_text_contents()
    for i, text in enumerate(texts):
        print(f"שורה {i+1}: {text}")
    
    # # run every second and update data without navigation
    # while True:
    #         try:
    #             data = await fetch_binance_data(page, db_symbol)
    #             if data:
    #                 price_doc = OrderBook(**data)
    #                 await price_doc.insert()
    #                 print(f"Inserted kraken {kraken_symbol} at {data['timestamp']}")
    #         except Exception as e:
    #             print(f"Error fetching data: {e}")
    #             traceback.print_exc()
    #         await asyncio.sleep(1) 


async def run_kraken_scraper(browser):
    tasks = [] 
    for db_symbol,kraken_symbol in kraken_symbols.items():
        task = asyncio.create_task(get_kraken_coin_order_book(kraken_symbol, db_symbol, browser))
        tasks.append(task)
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        print("🔴 Uncaught exception in tasks:", e)
