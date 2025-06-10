# dates
from datetime import datetime, timezone
from time import sleep, time
import json
import asyncio
import traceback
import logging
from typing import Dict, Any, Optional

from core.models import OrderBook
from utils.scraping_utils import wait_for_elements

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# # Updated symbols - removed duplicates and invalid pairs
# bit_stamp_symbols = {
#     "BTCUSD": "btcusd",      # Bitcoin
#     "ETHUSD": "ethusd",      # Ethereum
#     "LTCUSD": "ltcusd",      # Litecoin
#     "XRPUSD": "xrpusd",      # XRP
#     "BCHUSD": "bchusd",      # Bitcoin Cash

#     "ADAUSD": "adausd",      # Cardano
#     "SOLUSD": "solusd",      # Solana
#     "USDTUSD": "usdtusd",    # Tether
#     "USDCUSD": "usdcusd",    # USD Coin
#     "DOTUSD": "dotusd",      # Polkadot

#     "AVAXUSD": "avaxusd",    # Avalanche
#     "LINKUSD": "linkusd",    # Chainlink
#     "XLMUSD": "xlmusd",      # Stellar Lumens
#     "MATICUSD": "maticusd",  # Polygon
#     "UNIUSD": "uniusd",      # Uniswap

#     "AAVEUSD": "aaveusd",    # Aave
#     "COMPUSD": "compusd",    # Compound
#     "MKRUSD": "mkrusd",      # Maker
#     "GRTUSD": "grtusd",      # The Graph
# }

# Total: 95+ trading pairs available on Bitstamp



class BitstampDataProcessor:
    def __init__(self):
        self.retry_count = 3
        self.retry_delay = 5
        
    async def save_to_db(self, data: Dict[str, Any], exchange_name: str, exchange_symbol: str) -> bool:
        """Save data to database with error handling"""
        for attempt in range(self.retry_count):
            try:           
                price_doc = OrderBook(**data)
                await price_doc.insert()
                logger.info(f"✅ Inserted {exchange_name} {exchange_symbol} at {data['timestamp']}")
                return True
                
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed to save {exchange_symbol}: {e}")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"🔴 Failed to save {exchange_symbol} after {self.retry_count} attempts")
                    traceback.print_exc()
        return False

    def validate_json_structure(self, json_data: Dict[str, Any], symbol: str) -> bool:
        """Validate JSON structure with detailed error messages"""
        if not isinstance(json_data, dict):
            logger.error(f"❌ {symbol}: Received data is not a dictionary")
            return False
            
        if "data" not in json_data:
            logger.error(f"❌ {symbol}: Missing 'data' field in JSON")
            logger.debug(f"Available keys: {list(json_data.keys())}")
            return False
        
        data = json_data["data"]
        if not isinstance(data, dict):
            logger.error(f"❌ {symbol}: 'data' field is not a dictionary")
            return False
            
        required_fields = ["asks", "bids", "timestamp"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            logger.error(f"❌ {symbol}: Missing fields: {missing_fields}")
            logger.debug(f"Available fields in data: {list(data.keys())}")
            return False
            
        # Validate data types
        if not isinstance(data["asks"], list):
            logger.error(f"❌ {symbol}: 'asks' is not a list")
            return False
            
        if not isinstance(data["bids"], list):
            logger.error(f"❌ {symbol}: 'bids' is not a list")
            return False
            
        if not isinstance(data["timestamp"], (int, str)):
            logger.error(f"❌ {symbol}: 'timestamp' is not int or string")
            return False
            
        return True

    def process_order_book_data(self, json_data: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """Process order book data with validation"""
        try:
            data = json_data["data"]
            origin_asks = data["asks"]
            origin_bids = data["bids"]
            origin_time = int(data["timestamp"])
            
            # Validate that asks and bids have proper structure
            if not origin_asks and not origin_bids:
                logger.warning(f"⚠️ {symbol}: Both asks and bids are empty")
                
            # Convert to datetime in UTC format
            datetime_utc = datetime.fromtimestamp(origin_time, tz=timezone.utc)
            timestamp = datetime_utc.isoformat(timespec='milliseconds')
            
            asks = []
            bids = []
            
            # Process asks with validation
            for i, ask in enumerate(origin_asks):
                if not isinstance(ask, list) or len(ask) < 2:
                    logger.warning(f"⚠️ {symbol}: Invalid ask format at index {i}: {ask}")
                    continue
                try:
                    # Convert to float first to validate, then to string for Pydantic
                    price_float = float(ask[0])
                    amount_float = float(ask[1])
                    
                    # Validate that values are positive and reasonable
                    if price_float <= 0:
                        logger.warning(f"⚠️ {symbol}: Invalid ask price at index {i}: {price_float}")
                        continue
                    if amount_float <= 0:
                        logger.warning(f"⚠️ {symbol}: Invalid ask amount at index {i}: {amount_float}")
                        continue
                        
                    asks.append({"price": str(price_float), "amount": str(amount_float)})
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ {symbol}: Could not convert ask values at index {i}: {e}")
                    
            # Process bids with validation
            for i, bid in enumerate(origin_bids):
                if not isinstance(bid, list) or len(bid) < 2:
                    logger.warning(f"⚠️ {symbol}: Invalid bid format at index {i}: {bid}")
                    continue
                try:
                    # Convert to float first to validate, then to string for Pydantic
                    price_float = float(bid[0])
                    amount_float = float(bid[1])
                    
                    # Validate that values are positive and reasonable
                    if price_float <= 0:
                        logger.warning(f"⚠️ {symbol}: Invalid bid price at index {i}: {price_float}")
                        continue
                    if amount_float <= 0:
                        logger.warning(f"⚠️ {symbol}: Invalid bid amount at index {i}: {amount_float}")
                        continue
                        
                    bids.append({"price": str(price_float), "amount": str(amount_float)})
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ {symbol}: Could not convert bid values at index {i}: {e}")
                    
            processed_data = {
                "symbol": symbol,
                "exchange": "bitstamp",  # Fixed: was "byBit"
                "timestamp": timestamp,
                "bids": bids,
                "asks": asks
            }
            
            logger.debug(f"📊 {symbol}: Processed {len(asks)} asks, {len(bids)} bids")
            return processed_data
            
        except Exception as e:
            logger.error(f"❌ {symbol}: Error processing order book data: {e}")
            traceback.print_exc()
            return None

async def get_bit_stamp_coin_order_book(bit_stamp_symbol: str, db_symbol: str, context, processor: BitstampDataProcessor):
    """Enhanced function with better error handling"""
    page = None
    try:
        page = await context.new_page()
        logger.info(f"🚀 Starting scraper for {bit_stamp_symbol}")
        
        def on_websocket(ws):
            order_books_string = ""
            last_save_time = 0
            consecutive_errors = 0
            max_consecutive_errors = 10

            async def process_data():
                nonlocal order_books_string, consecutive_errors
                
                if not order_books_string:
                    logger.warning(f"⚠️ {bit_stamp_symbol}: Empty data string")
                    return
                
                try:
                    # Parse JSON with error handling
                    json_data = json.loads(order_books_string)
                    
                    # Validate structure
                    if not processor.validate_json_structure(json_data, bit_stamp_symbol):
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            logger.error(f"🔴 {bit_stamp_symbol}: Too many consecutive errors, stopping")
                            return
                        return
                    
                    # Process data
                    processed_data = processor.process_order_book_data(json_data, db_symbol)
                    if processed_data is None:
                        consecutive_errors += 1
                        return
                    
                    # Save to database
                    success = await processor.save_to_db(
                        data=processed_data, 
                        exchange_name="bitstamp", 
                        exchange_symbol=bit_stamp_symbol
                    )
                    
                    if success:
                        consecutive_errors = 0  # Reset on success
                    else:
                        consecutive_errors += 1

                except json.JSONDecodeError as e:
                    logger.error(f"❌ {bit_stamp_symbol}: JSON decode error: {e}")
                    logger.debug(f"Raw data: {order_books_string[:200]}...")
                    consecutive_errors += 1
                    
                except Exception as e:
                    logger.error(f"❌ {bit_stamp_symbol}: Unexpected error in process_data: {e}")
                    traceback.print_exc()
                    consecutive_errors += 1
        
            async def on_frame_received(payload: str):
                nonlocal order_books_string, last_save_time
                
                try:
                    now = time()
                    
                    if now - last_save_time >= 1:  
                        if f'"channel":"order_book_{bit_stamp_symbol}"' in payload:
                            order_books_string = payload
                            last_save_time = now
                            asyncio.create_task(process_data())
                            
                except Exception as e:
                    logger.error(f"❌ {bit_stamp_symbol}: Error in frame handler: {e}")

            ws.on("framereceived", on_frame_received)

        page.on("websocket", on_websocket)

        # Navigate to page with timeout
        url = f"https://www.bitstamp.net/trade/{bit_stamp_symbol}"
        logger.info(f"🌐 Navigating to {url}")
        
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        logger.info(f"✅ Successfully loaded page for {bit_stamp_symbol}")
        
        # Keep the connection alive
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ {bit_stamp_symbol}: Error in main function: {e}")
        traceback.print_exc()
        
    finally:
        if page:
            try:
                await page.close()
                logger.info(f"🔚 Closed page for {bit_stamp_symbol}")
            except Exception as e:
                logger.error(f"❌ Error closing page for {bit_stamp_symbol}: {e}")

async def run_bit_stamp_scraper_v2(context):
    """Enhanced scraper runner with better error handling"""
    processor = BitstampDataProcessor()
    tasks = []
    
    logger.info(f"🚀 Starting Bitstamp scraper for {len(bit_stamp_symbols)} symbols")
    
    for db_symbol, bit_stamp_symbol in bit_stamp_symbols.items():
        task = asyncio.create_task(
            get_bit_stamp_coin_order_book(bit_stamp_symbol, db_symbol, context, processor),
            name=f"bitstamp_{bit_stamp_symbol}"
        )
        tasks.append(task)
        
        # Add small delay to avoid overwhelming the server
        await asyncio.sleep(0.1)
    
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        for i, result in enumerate(results):
            symbol = list(bit_stamp_symbols.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"❌ Task for {symbol} failed: {result}")
            else:
                logger.info(f"✅ Task for {symbol} completed")
                
    except Exception as e:
        logger.error(f"🔴 Uncaught exception in scraper: {e}")
        traceback.print_exc()
    
    logger.info("🏁 Bitstamp scraper finished")