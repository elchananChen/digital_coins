# dates
from datetime import datetime, timezone

# for async 
import asyncio

# for errors track
import traceback

from core.models import OrderBook


crypto_symbols = {
    "BTCUSDT":"BTC_USDT", 
    "ETHUSDT":"ETH_USDT", 
    "LTCUSDT":"LTC_USDT", 
    # "XRPUSDT":"XRP_USDT", 
    # "BCHUSDT":"BCH_USDT", 
}


# row-ask/bids = e-list-item

# ask container = e-list e-order-book-list e-order-book-asks-list
# bids container = e-list e-order-book-list e-order-book-bids-list


# span price = e-number-dim text-success-default
# span amount = e-number-dim

async def fetch_crypto_data(page,db_symbol):
        try:
            asks_container = page.locator("//div[@class='e-list e-order-book-list e-order-book-asks-list']")
            bids_container = page.locator("//div[@class='e-list e-order-book-list e-order-book-bids-list']")
            
            rows_asks = asks_container.locator("//div[@class='e-list-item']")
            rows_bids = bids_container.locator("//div[@class='e-list-item']")
            
            count = await rows_asks.count()
            now = datetime.now(timezone.utc)
            asks = []
            bids = []
            for i in range(count):
                row_asks = rows_asks.nth(i)
                row_bids = rows_bids.nth(i)


                ask_price = await row_asks.locator("//span[contains(@class, 'e-number-dim')]").nth(0).inner_text()
                ask_amount = await row_asks.locator("//span[contains(@class, 'e-number-dim')]").nth(1).inner_text()

                bid_price = await row_bids.locator("//span[contains(@class, 'e-number-dim')]").nth(0).inner_text()
                bid_amount = await row_bids.locator("//span[contains(@class, 'e-number-dim')]").nth(1).inner_text()

                ask =  {"price": ask_price.replace(',', ''),"amount": ask_amount.replace(',', '')}
                bid =  {"price": bid_price.replace(',', ''),"amount": bid_amount.replace(',', '')}

                asks.append(ask)
                bids.append(bid)


            data = { "symbol": db_symbol,"exchange": "cryptoDotCom", "timestamp":now, "bids": bids,"asks": asks }
            print(data)
            return data
        except TimeoutError:
            print("❌ Element did not appear in time – maybe the page is slow or the XPath is incorrect")
            traceback.print_exc()
        except Exception as e:
            print(f"❗ Unexpected error: {e}")





# go to the relevant page to one coin, 
# get the wrapper div, wait for  for the first ask to avoid non existing element error
# exc fetch_binance_data function every second

async def get_crypto_coin_order_book(crypto_symbol,db_symbol, browser):
    page = await browser.new_page()
    await page.goto(f"https://crypto.com/exchange/trade/{crypto_symbol}", wait_until="domcontentloaded")
    
    # wait for the first ask to load and wait one more second
    ask_light_object = page.locator("//div[@class='e-order-book-last-column']")
    await ask_light_object.first.wait_for(timeout=20000)
    await asyncio.sleep(1)
    print(await ask_light_object.inner_text())
    
    # run every second and update data without navigation
    while True:
            try:
                data = await fetch_crypto_data(page, db_symbol)
                if data:
                    price_doc = OrderBook(**data)
                    await price_doc.insert()
                    print(f"Inserted crypto.com {crypto_symbol} at {data['timestamp']}")
            except Exception as e:
                print(f"Error fetching data: {e}")
                traceback.print_exc()
            await asyncio.sleep(1) 


async def run_crypto_scraper(browser):
    tasks = [] 
    for db_symbol,crypto_symbol in crypto_symbols.items():
        task = asyncio.create_task(get_crypto_coin_order_book(crypto_symbol, db_symbol, browser))
        tasks.append(task)
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        print("🔴 Uncaught exception in tasks:", e)
