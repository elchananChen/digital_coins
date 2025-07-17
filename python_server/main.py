import asyncio
import logging
import uuid
import psutil
import os
from core import init_redis_client 

# pydantic models (classes)  
from monitoring.utils import monitoring_loop, generate_and_log_scrape_summaries
from monitoring.global_metric_dicts import EXCHANGES_METRICS

from patchright.async_api import async_playwright

from exchanges.bit_stamp import run_bit_stamp_scraper


# Configure logging
logger = logging.getLogger(__name__)

RUN_ID = str(uuid.uuid4())
CURRENT_PROCESS = psutil.Process(os.getpid())


# delay to each task for soft initialization 
delay_per_task = 10

event = asyncio.Event()

exchanges = [
    {
        "name": "bitStamp",
        "fn": run_bit_stamp_scraper,
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
async def main(event:asyncio.Event,run_id:str):
    logger.info("Scraper main process started")
    # connect to redis
    redis_client = await init_redis_client()
    if not redis_client:
        logger.critical("Failed to connect to Redis. Exiting.")
        raise ConnectionError("Failed to connect to Redis.")
 
    async with async_playwright() as p:

        # process monitor
        asyncio.create_task(
            monitoring_loop(
                run_id=RUN_ID,
                current_process=CURRENT_PROCESS,
                interval_sec=60,
                logger=logger
                ))
        
        asyncio.create_task(
            generate_and_log_scrape_summaries(
                exchange_metrics=EXCHANGES_METRICS, 
                interval_delay=60,
                logger=logger
                ))

        tasks =[]

        for exchange in exchanges:
            # background browser
            headless_browser = await p.chromium.launch(
                headless=True,
                args=exchange.get("browser_args", []),
                )
            exchange_context =  await headless_browser.new_context(
                **exchange.get("context_options", {}),
            )
            exchange_name = exchange["name"]
            logger.info(f"Launching browser for {exchange_name}")
            
            task = asyncio.create_task(
                exchange["fn"](
                    exchange_context,
                    redis_client,
                    exchange_name=exchange["name"],
                    event=event,
                    delay_per_task=delay_per_task,
                    run_id=run_id
                    ))
            tasks.append(task)


        try:
            logger.info(f"All scraper tasks created for {len(exchanges)} exchanges")
            await asyncio.gather(*tasks,return_exceptions=True)
            logger.info(f"Scraper tasks gathered successfully")

        except KeyboardInterrupt as e:
            logger.info(f"🛑 Graceful shutdown completed (run id: {run_id})")


        except Exception as e:
            logger.critical("Fatal error during task gathering \n Exception: {e}")

        finally:
            if redis_client:
                try:
                    await redis_client.aclose()
                    await redis_client.connection_pool.disconnect() 
                    logger.info("Redis connection closed.")
                except Exception as e:
                    logger.error(f"Failed to close Redis connection \n Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main(event,RUN_ID))