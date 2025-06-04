import asyncio
from core import init_db, start_monitoring
from exchanges.binance import run_binance_scraper
from exchanges.kraken import run_kraken_scraper
from exchanges.crypto_dot_com import run_crypto_scraper
from playwright.async_api import async_playwright
platforms = [
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
    start_monitoring()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False,args=["--start-maximized"])

        # binance_browser = await p.chromium.launch(headless=True)
        # kraken_context = await browser.new_context(no_viewport=True)
        crypto_context = await browser.new_context(no_viewport=True)
        # await run_binance_scraper(binance_browser)
        await run_crypto_scraper(crypto_context)

if __name__ == "__main__":
    asyncio.run(main())