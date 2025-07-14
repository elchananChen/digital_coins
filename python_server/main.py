import asyncio
import logging
import uuid


from core import init_redis_client 


from exchanges.by_bit import run_by_bit_scraper

from exchanges.bit_stamp import run_bit_stamp_scraper

# decorators and monitoring functions
from monitoring.utils import time_async_function

# pydantic models (classes)  
from monitoring.models import ScraperRunSummary,CloseStatusEnum

from patchright.async_api import async_playwright


from utils import aggregate_scraper_results

# Configure logging
logger = logging.getLogger(__name__)

run_id = str(uuid.uuid4())



# delay to each task for soft initialization 
delay_per_task =1

event = asyncio.Event()
exchanges = [
    {
        "name": "bitStamp",
        "fn": run_bit_stamp_scraper,
        "headless": True,
        "browser_args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-gpu",
            "--disabl"
            ],
        "context_options": {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080},
            "is_mobile": False,
            }
    },
]

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
 
    async with async_playwright() as p:
        global run_summary_data
        tasks =[]
       
        for exchange in exchanges:
            # background browser
            
            if exchange["headless"] == True:
                headless_browser = await p.chromium.launch(
                    headless=True,
                    args=exchange.get("browser_args", []),
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
            results = await asyncio.gather(*tasks,return_exceptions=True)

            #  stop the stop task if not finished

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