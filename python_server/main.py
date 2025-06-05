import asyncio
from core import init_db, start_monitoring_v1, start_monitoring_v2 ,start_monitoring_v3 
from exchanges.binance import run_binance_scraper
from exchanges.kraken import run_kraken_scraper
from playwright.async_api import async_playwright
exchanges = [
    {
        "name": "binance",
        "fn": run_binance_scraper,
        "headless": True,
    },
    {
        "name": "kraken",
        "fn": run_kraken_scraper,
        "headless": False,
    },
]

async def main():
    await init_db()
    # start_monitoring_v1()
    # start_monitoring_v2()
    start_monitoring_v3()

    async with async_playwright() as p:
        tasks =[]        
        for exchange in exchanges:
            if exchange["headless"] == True:
                headless_browser = await p.chromium.launch(headless=True)              
                exchange_context =  await headless_browser.new_context()    
            else:
                browser = await p.chromium.launch(headless=False,args=["--start-maximized"])
                exchange_context = await browser.new_context(no_viewport=True)
            task = asyncio.create_task(exchange["fn"](exchange_context))
            tasks.append(task)    
        try:
            await asyncio.gather(*tasks,return_exceptions=True)   
        except Exception as e:
            print("🔴 Uncaught exception in tasks:", e)

            

if __name__ == "__main__":
    asyncio.run(main())