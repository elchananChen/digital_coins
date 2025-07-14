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



if environment == "dev":
    load_dotenv('.dev.env', override=True)
    REDIS_HOST = os.getenv('REDIS_HOST')
    print(f"REDIS_HOST: {REDIS_HOST}")
    print("Loaded environment variables from .dev.env for local testing.")
else:
    REDIS_HOST = os.getenv('REDIS_HOST')
    print(f"REDIS_HOST: {REDIS_HOST}")
    print("Running in non-local testing environment. Relying on existing environment variables.")


