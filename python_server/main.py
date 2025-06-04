import asyncio
from core import init_db, start_monitoring
from exchanges.binance import run_binance_scraper
from exchanges.kraken import run_kraken_scraper
from playwright.async_api import async_playwright

async def main():
    await init_db()
    # start_monitoring()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        await run_binance_scraper(browser)
        # await run_kraken_scraper(browser)

if __name__ == "__main__":
    asyncio.run(main())
