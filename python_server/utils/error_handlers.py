# build in
import logging
import json
from typing import Optional

# redis
from redis import exceptions

# playwright
from playwright._impl._errors import Error as PlaywrightError, TargetClosedError, TimeoutError as PlaywrightTimeoutError


logger = logging.getLogger(__name__)

def log_and_categorize_playwright_error(e: PlaywrightError, symbol: str, error_summary: dict, page_created: bool = False):
    """
    Logs and categorizes a PlaywrightError, updating the error_summary dictionary.
    :param e: The PlaywrightError instance.
    :param symbol: The currency pair symbol for logging.
    :param error_summary: The dictionary to update with error counts.
    :param page_created: True if a page object was successfully created before the error.
    """
    error_message = str(e)

    def _update_error_count(error_type_key: str):
        error_summary[error_type_key] = error_summary.get(error_type_key, 0) + 1

    if isinstance(e, PlaywrightTimeoutError): # This catch is for when TimeoutError is caught by PlaywrightError
        logger.debug(f"❌ {symbol}: Navigation TimeoutError: {e}")
        _update_error_count("playwright_navigation_timeout")
    elif isinstance(e, TargetClosedError):
        logger.debug(f"❌ {symbol}: Playwright TargetClosedError: Browser/Context/Page was closed during operation: {e}")
        _update_error_count("playwright_target_closed")
    elif not page_created: # Error occurred before page was successfully created
        logger.debug(f"❌ {symbol}: Playwright: Failed to open new page: {e}")
        _update_error_count("playwright_new_page_failed")
    elif "ERR_INVALID_URL" in error_message:
        logger.debug(f"❌ {symbol}: Playwright: Invalid URL provided for navigation: {e}")
        _update_error_count("playwright_invalid_url")
    elif "ERR_CERT" in error_message:
        logger.debug(f"❌ {symbol}: Playwright: SSL Certificate error during navigation: {e}")
        _update_error_count("playwright_ssl_cert_error")
    elif "net::ERR_INTERNET_DISCONNECTED" in error_message:
        logger.debug(f"❌ {symbol}: Playwright: Internet disconnected during operation: {e}")
        _update_error_count("playwright_internet_disconnected")
    else:
        logger.debug(f"❌ {symbol}: Playwright: Other error during operation: {e}")
        _update_error_count("playwright_general_op_failed")

def log_general_exception(e: Exception, symbol: str, error_summary: dict):
    """
    Logs general Python exceptions and updates the error_summary dictionary.
    """
    logger.debug(f"❌ {symbol}: Unexpected general error: {e}")
    error_summary["general_scraper_exception"] = error_summary.get("general_scraper_exception", 0) + 1


# --- Function to handle process_data errors ---
def log_and_categorize_websocket_data_error(symbol: str,exchange:str, error_summary: dict, is_json_decode_error: bool = False, is_missing_keys_error: bool = False, is_validation_error: bool = False,is_empty_data_error: bool = False, e: Optional[Exception]= None) -> str:
    """
    Logs and categorizes errors occurring during WebSocket data processing (inside process_data).
    Updates the error_summary dictionary and returns a string detailing the error.
    :param e: The exception instance.
    :param symbol: The currency pair symbol for logging.
    :param error_summary: The dictionary to update with error counts.
    :param is_json_decode_error: True if the error is specifically a JSONDecodeError.
    :param is_missing_keys_error: True if the error is due to missing expected keys in JSON data.
    :param is_validation_error: True if the error is due to data validation failure (e.g., empty asks/bids).
    """

    error_type_key = "websocket_general_processing_error" # Default
    if e:
        error_message = str(e)
        detailed_error_message = f"WebSocket data processing error: {error_message}"

    def _update_error_count(key: str):
        error_summary[key] = error_summary.get(key, 0) + 1

    if is_json_decode_error or isinstance(e, json.JSONDecodeError):
        error_type_key = "websocket_json_decode_error"
        detailed_error_message = f"WebSocket JSON decoding error: {error_message}"
    elif is_missing_keys_error or isinstance(e, KeyError): # Often missing keys manifest as KeyError
        error_type_key = "websocket_missing_data_keys"
        detailed_error_message = f"WebSocket data missing expected keys: {error_message}"
    elif is_empty_data_error : # Often missing keys manifest as KeyError
        error_type_key = "websocket_empty_data"
        detailed_error_message = f"WebSocket empty data expected keys: {error_message}"
    elif is_validation_error:
        error_type_key = "websocket_data_validation_failed"
        detailed_error_message = f"WebSocket data validation failed: {error_message}"

    logger.debug(f"❌ {symbol}@{exchange}: {error_type_key.replace('_', ' ').title()}: {detailed_error_message}")
    _update_error_count(error_type_key)
    # traceback.print_exc() # Still useful for debugging internal processing errors
    return detailed_error_message


# --- Function to handle redis errors ---
def log_and_categorize_redis_error(e: Exception, symbol: str,exchange:str, error_summary: dict) -> str:
    """
    Logs and categorizes Redis-specific exceptions.
    Updates the error_summary dictionary and returns a string detailing the error.
    :param e: The exception instance.
    :param symbol: The currency pair symbol associated with the Redis operation.
    :param error_summary: The dictionary to update with error counts.
    """
    error_message = str(e)
    error_type_key = "redis_general_error" # Default error type
    detailed_error_message = f"Redis error: {error_message}"

    def _update_error_count(key: str):
        error_summary[key] = error_summary.get(key, 0) + 1

    if isinstance(e, exceptions.ConnectionError):
        error_type_key = "redis_connection_error"
        detailed_error_message = f"Redis connection error: {error_message}"
    elif isinstance(e, exceptions.TimeoutError): # Can be a subset of ConnectionError, but good to differentiate
        error_type_key = "redis_timeout_error"
        detailed_error_message = f"Redis operation timed out: {error_message}"
    elif isinstance(e, exceptions.DataError):
        error_type_key = "redis_data_error"
        detailed_error_message = f"Redis data/protocol error: {error_message}"
    elif isinstance(e, exceptions.ReadOnlyError): # Specific to Redis cluster/replica issues
        error_type_key = "redis_readonly_error"
        detailed_error_message = f"Redis in read-only mode: {error_message}"

    logger.debug(f"❌ {symbol}@{exchange}: {error_type_key.replace('_', ' ').title()}: {detailed_error_message}")
    _update_error_count(error_type_key)
    return detailed_error_message