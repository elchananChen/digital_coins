# dates
from datetime import datetime, timezone

# for async 
import asyncio

# for errors track
import traceback

from core.models import OrderBook


binance_symbols = {
    "BTCUSDT":"BTC_USDT", 
    "ETHUSDT":"ETH_USDT", 
    "LTCUSDT":"LTC_USDT", 
    "XRPUSDT":"XRP_USDT", 
    "BCHUSDT":"BCH_USDT", 
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





# go to the relevant page to one coin, 
# get the wrapper div, wait for  for the first ask to avoid non existing element error
# exc fetch_binance_data function every second

async def get_binance_coin_order_book(binance_symbol,db_symbol, browser):
    page = await browser.new_page()
    await page.goto(f"https://www.binance.com/en/trade/{binance_symbol}?_from=markets&type=spot", wait_until="domcontentloaded")

    # wait for the first ask to load and wait one more second
    ask_light_object = page.locator("css=div.ask-light")
    await ask_light_object.first.wait_for(timeout=20000)
    await asyncio.sleep(1)

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


async def run_binance_scraper(browser):
    tasks = [] 
    for db_symbol,binance_symbol in binance_symbols.items():
        task = asyncio.create_task(get_binance_coin_order_book(binance_symbol, db_symbol, browser))
        tasks.append(task)
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        print("🔴 Uncaught exception in tasks:", e)


    