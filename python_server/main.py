import asyncio
import logging

from core import init_db, start_monitoring_v1, start_monitoring_v2 ,start_monitoring_v3 ,init_redis_client 


from exchanges.binance import run_binance_scraper
from exchanges.kraken import run_kraken_scraper
from exchanges.by_bit import run_by_bit_scraper
from exchanges.crypto_dot_com import run_crypto_scraper
from exchanges.bit_stamp import run_bit_stamp_scraper
from exchanges.bitstamp_v2 import run_bit_stamp_scraper_v2


from playwright.async_api import async_playwright


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



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
    # {
    #     "name": "byBit",
    #     "fn": run_by_bit_scraper,
    #     "headless": False,
    # },
    {
        "name": "bitStamp",
        "fn": run_bit_stamp_scraper,
        # "fn": run_bit_stamp_scraper_v2,
        "headless": False,
    }
]



async def main():
    await init_db()
    # start_monitoring_v1()
    # start_monitoring_v2()
    # start_monitoring_v3()
    redis_client = await init_redis_client()
    if not redis_client:
        print("Error: Could not connect to Redis. Exiting.")
        return

    async with async_playwright() as p:
        tasks =[]        
        for exchange in exchanges:
            # background browser
            if exchange["headless"] == True:
                headless_browser = await p.chromium.launch(headless=True)              
                exchange_context =  await headless_browser.new_context()    
            # front browser
            else:
                browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
                exchange_context = await browser.new_context(no_viewport=True)
            
            task = asyncio.create_task(exchange["fn"](exchange_context,redis_client))
            tasks.append(task)
        try:
            await asyncio.gather(*tasks,return_exceptions=True)
        except KeyboardInterrupt:
            logger.info("🛑 Graceful shutdown completed")
            if redis_client:
               await redis_client.close()
               await redis_client.connection_pool.disconnect() 
               print("Redis connection closed.")

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            if redis_client:
               await redis_client.close()
               await redis_client.connection_pool.disconnect() 
               print("Redis connection closed.")

if __name__ == "__main__":
    asyncio.run(main())