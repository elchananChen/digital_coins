# dates
from datetime import datetime, timezone

import asyncio
import logging
import traceback

from core.models import OrderBook
from monitoring.utils import time_async_function

from utils import (
    log_and_categorize_playwright_error,
    log_general_exception,
    log_and_categorize_websocket_data_error,
    merge_addition_dicts,
    add_overall_exchange_status
    )

from monitoring.utils import (
    time_async_function,
    send_metric_log
)

from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError  
from monitoring.models import ExchangeScrapeReport, ExchangeCurrencyEvent

crypto_symbols = {
    "BTCUSDT":"BTC_USDT", 
    "ETHUSDT":"ETH_USDT", 
    "LTCUSDT":"LTC_USDT", 
    "XRPUSDT":"XRP_USDT", 
    "BCHUSDT":"BCH_USDT", 
}
logger = logging.getLogger(__name__)

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

                ask =  [ask_price.replace(',', ''), ask_amount.replace(',', '')]
                bid =  [bid_price.replace(',', ''), bid_amount.replace(',', '')]

                asks.append(ask)
                bids.append(bid)


            data = { "symbol": db_symbol,"exchange": "cryptoDotCom", "timestamp":now, "bids": bids,"asks": asks }
            # print(data)
            return data
        except TimeoutError:
            print("❌ Element did not appear in time – maybe the page is slow or the XPath is incorrect")
            traceback.print_exc()
        except Exception as e:
            print(f"❗ Unexpected error: {e}")


# go to the relevant page to one coin, 
# get the wrapper div, wait for  for the first ask to avoid non existing element error
# exc fetch_binance_data function every second
async def get_crypto_coin_order_book(
            crypto_symbol,
            db_symbol, 
            context, 
            redis_client,
            exchange_name,
            event,
            sleep_time,
            run_id
            ):
   
    page = await context.new_page()
    await page.goto(f"https://crypto.com/exchange/trade/{crypto_symbol}", wait_until="domcontentloaded")
    
    # wait for the first ask to load and wait one more second
    ask_light_object = page.locator("//div[@class='e-order-book-last-column']")
    await ask_light_object.first.wait_for(timeout=20000)
    await asyncio.sleep(1)
    # print(await ask_light_object.inner_text())

    # run every second and update data without navigation
    while event.is_set:
            try:
                data = await fetch_crypto_data(page, db_symbol)
                if data:
                    price_doc = OrderBook(**data)
                    # await price_doc.insert()
                    print(f"Inserted crypto.com {crypto_symbol} at {data['timestamp']}")
            except Exception as e:
                print(f"Error fetching data: {e}")
                traceback.print_exc()
            await asyncio.sleep(sleep_time)

@time_async_function(component_name="scraper_run", event_name="exchange_scrape_duration")
async def run_crypto_scraper(context , redis_client,exchange_name,event,delay_per_task,run_id):
    monitor_data = {
        "total_currency_pairs_configured": len(crypto_symbols),
        "successful_currency_pair_initializations": 0,
        "failed_currency_pair_initializations":0,

        # --- Data Volume and Quality Metrics ---
        "total_data_points_sent_to_redis":0,
        "errors_summary":{}
    }

    tasks = []
    results = []
    logger.info(f"Total symbols: {len(crypto_symbols)}")

    for i ,(db_symbol,crypto_symbol) in enumerate(crypto_symbols.items()):
        sleep_time = i * delay_per_task
        task = asyncio.create_task(get_crypto_coin_order_book(
            crypto_symbol=crypto_symbol, 
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
        logger.error(f"🔴 Uncaught critical exception in run_bit_stamp_scraper: {e}")

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