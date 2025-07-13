import asyncio
import logging
import uuid
import os

from core import init_redis_client 


from exchanges.binance import run_binance_scraper
from exchanges.kraken import run_kraken_scraper
from exchanges.by_bit import run_by_bit_scraper
from exchanges.crypto_dot_com import run_crypto_scraper
from exchanges.bit_stamp import run_bit_stamp_scraper

# decorators and monitoring functions
from monitoring.utils import time_async_function, scraper_run_summary_logger,handle_async_errors

# pydantic models (classes)  
from monitoring.models import ScraperRunSummary,CloseStatusEnum

from patchright.async_api import async_playwright
from playwright_stealth import Stealth 
from dotenv import load_dotenv

from utils import aggregate_scraper_results


from config import environment


# Configure logging
logger = logging.getLogger(__name__)


if environment == "dev":
    load_dotenv('.dev.env', override=True)
    REDIS_HOST = os.getenv('REDIS_HOST')
    print(f"REDIS_HOST: {REDIS_HOST}")
    print("Loaded environment variables from .dev.env for local testing.")
else:
    REDIS_HOST = os.getenv('REDIS_HOST')
    print(f"REDIS_HOST: {REDIS_HOST}")
    print("Running in non-local testing environment. Relying on existing environment variables.")


run_id = str(uuid.uuid4())
# run duration for dev (for production put "inf" or remove the "stop_task")
duration = 90

# delay to each task for soft initialization 
delay_per_task =0.2

event = asyncio.Event()
exchanges = [
    # {
    #     "name": "binance",
    #     "fn": run_binance_scraper,
    #     "headless": True,
    # },
    # {
    #     "name": "kraken",
    #     "fn": run_kraken_scraper,
    #     "headless": False,
    # },
    # {
    #     "name": "cryptoDotCom",
    #     "fn": run_crypto_scraper,
    #     "headless": False,
    # },
    {
        "name": "byBit",
        "fn": run_by_bit_scraper,
        # "headless": False,
        "headless": True,
       
        "browser_args": [
            "--no-sandbox",
            # "--disable-setuid-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage", 
            # "--no-zygote",             
            # "--single-process",        
            "--disable-blink-features=AutomationControlled", 
            "--remote-debugging-port=9222",
            ], 
            "context_options": {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080},
            "is_mobile": False,
            "locale": "he-IL",
            "timezone_id": "Asia/Jerusalem", 
            # "ignore_https_errors": True, 
            },
        "use_stealth": True
    },
#     {
#         "name": "bitStamp",
#         "fn": run_bit_stamp_scraper,
#         # "fn": run_bit_stamp_scraper_v2,
#         "headless": True,
#         "browser_args": [
#             "--no-sandbox",
#             "--disable-setuid-sandbox",
#             "--disable-gpu",
#             "--disabl"
#             ],
#         "context_options": {
#             "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#             "viewport": {"width": 1920, "height": 1080}, # standard resolution
#             "is_mobile": False,
#             }
#     },
]

# monitoring initializations

async def stop_event(event: asyncio.Event):
    await asyncio.sleep(duration)
    event.set()

# Apply the decorators directly to the main function.
# time_async_function will handle calculating duration and sending ScraperRunSummary.
# handle_async_errors will catch unhandled exceptions in main and send an error log.
# @handle_async_errors(component_name="Scraper Main Process", is_critical=True)
@time_async_function(component_name="Scraper Main Process", event_name="Full Scraper Run")
async def main(event:asyncio.Event,run_id:str):
    # connect to redis
    redis_client = await init_redis_client()
    if not redis_client:
        print("Error: Could not connect to Redis. Exiting.")
        raise ConnectionError("Failed to connect to Redis.")
 
    # async with Stealth().use_async(async_playwright()) as p:
    async with async_playwright() as p:
        global run_summary_data
        tasks =[]
       
        for exchange in exchanges:
            # background browser
            
            if exchange["headless"] == True:
                headless_browser = await p.chromium.launch(
                    headless=True,
                    args=exchange.get("browser_args", []),
                    channel="chrome"
                    )
                exchange_context =  await headless_browser.new_context(
                   **exchange.get("context_options", {}),
                )
            else:
                browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
                exchange_context = await browser.new_context(no_viewport=True)
            
            task = asyncio.create_task(exchange["fn"](exchange_context,redis_client,exchange_name=exchange["name"],event=event,delay_per_task=delay_per_task,run_id=run_id))
            tasks.append(task)
        results = []

        try:
            # run time for the program
            stop_task = asyncio.create_task(stop_event(event=event))       

            results = await asyncio.gather(*tasks,return_exceptions=True)

            #  stop the stop task if not finished
            if not stop_task.done():
                stop_task.cancel()
                try:
                    # wait for the stop_task.cancel() to fullfil
                    await stop_task
                except asyncio.CancelledError:
                    pass 

            run_summary_data = await aggregate_scraper_results(
                all_exchange_results=results,
                total_exchanges_configured= len(exchanges),
                close_status=CloseStatusEnum.planned_shutdown,
                run_id=run_id
                )
            return ScraperRunSummary(**run_summary_data)
        
        except KeyboardInterrupt as e:
            logger.info("🛑 Graceful shutdown completed")
            run_summary_data = await aggregate_scraper_results(
                all_exchange_results=results,
                total_exchanges_configured= len(exchanges),
                close_status=CloseStatusEnum.planned_shutdown,
                run_id=run_id
                )

            return ScraperRunSummary(**run_summary_data)
        
        except Exception as e:
            logger.error(f"Fatal error during gather: {e}")
            run_summary_data = await aggregate_scraper_results(
                all_exchange_results=results,
                total_exchanges_configured= len(exchanges),
                close_status=CloseStatusEnum.unplanned_shutdown,
                run_id=run_id
                )

            return ScraperRunSummary(**run_summary_data)
        
        finally:
            if redis_client:
                try:
                    await redis_client.aclose()
                    await redis_client.connection_pool.disconnect() 
                    logger.info("Redis connection closed.")
                except Exception as e:
                    logger.error(f"Error closing Redis connection: {e}")

if __name__ == "__main__":
    asyncio.run(main(event,run_id))