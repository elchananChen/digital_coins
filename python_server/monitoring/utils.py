# monitors/utils.py
import logging
import logging.handlers
import time
import asyncio
import functools
import os
import socket
import sys
import redis
from datetime import datetime, timezone 
import structlog


from monitoring.models import (
    BaseMonitoringEvent,
    ExchangeScrapeReport,
    ScraperRunSummary,
    ExchangeCurrencyEvent,
    ScraperProcessResourceMetric,
    DBWorkerHeartbeatEvent,
    DBWorkerBatchFlushEvent,
    ErrorDetails,
)

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
# --- 1. define structlog (and logging) basic definition ---
'''
 Set up logging in its simplest form,
 allowing structlog to control the log formatting
'''
logging.basicConfig(
    format="%(message)s", # final format for structlog 
    # stream=sys.stdout, # or sys.stderr, or a log file, depending on the final configuration
    level=logging.DEBUG, # minimum log level
    handlers=[]
)

# for adding "host_id" to all logs
def add_host_id(_, _method_name, event_dict):
    """Adds the hostname to the event dict."""
    event_dict["host_id"] = socket.gethostname()
    return event_dict

# Global structlog processors
# These processors will run for every log produced via structlog
PROCESSORS_PRE_RENDER = [
    structlog.stdlib.add_logger_name,  # Adds the logger name
    structlog.stdlib.add_log_level,    # Adds the log level (INFO, ERROR, etc.)
    structlog.processors.TimeStamper(fmt="iso", utc=True), # Adds a timestamp in ISO format in UTC
    add_host_id, # Custom processor to add Host ID
    structlog.processors.StackInfoRenderer(), # Adds stack info for errors
    structlog.processors.format_exc_info, # Adds exception information to the log
    # structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
]

structlog.configure(
    processors=[
        *PROCESSORS_PRE_RENDER,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter
        ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


# --- Setup file logger ---
def setup_file_logger(name: str, filename: str, level=logging.INFO):
    """
    Helper function to set up a logger for writing to a file with rotation.
    - name: The name of the logger (e.g., 'scraper.events'). This is the name of the logger within the standard logging system.
    - filename: The name of the file where logs will be saved (e.g., 'scraper_events.log').
    - level: The minimum logging level to be printed for this logger (e.g., logging.INFO).
    """
    # 1. Create an instance of the standard Python logger
    std_logger = logging.getLogger(name)
    std_logger.setLevel(level)
    # Clear previous handlers to prevent duplicates if the function is called multiple times
    std_logger.handlers = []

    # Prevent logs from this specific logger from propagating to parent loggers
    std_logger.propagate = False 

         
    # 2. Create a formatter that will work with structlog
    # We will use structlog's JSONRenderer so that logs are in JSON format in the file.
    # The foreign_pre_chain ensures that global structlog processors are applied.
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=PROCESSORS_PRE_RENDER,
    )

    # 3. Configure the handler for writing to a file with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, filename), # Full path to the log file
        maxBytes=10 * 1024 * 1024,       # 10 MB - maximum size before rotation
        backupCount=5                    # Keep 5 old backup files
    )
    file_handler.setFormatter(file_formatter) # Set the formatter for the handler
    file_handler.setLevel(level)
   
    std_logger.addHandler(file_handler) # Add the handler to the standard logger
    # file_handler.flush()

    # 4. Return a structlog logger instance linked to the standard logger we configured.
    # This is the logger you will use in your code.
    return structlog.get_logger(name)

# ---  Setup a general logger for console output and a general log file ---
# 1 structlog-compatible formatter for the general log file
general_file_formatter = structlog.stdlib.ProcessorFormatter(
    processor=structlog.processors.JSONRenderer(),
    foreign_pre_chain=PROCESSORS_PRE_RENDER,
)
# 2. Create a RotatingFileHandler for general logs
general_file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(LOG_DIR, "general_scraper.log"),
    maxBytes=10 * 1024 * 1024,
    backupCount=5
)

general_file_handler.setFormatter(general_file_formatter)

# 3. Create a structlog-compatible formatter for console output
console_formatter = structlog.stdlib.ProcessorFormatter(
    processor=structlog.dev.ConsoleRenderer(),
    foreign_pre_chain=PROCESSORS_PRE_RENDER,
)

# 4. Create a StreamHandler for console output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_formatter)

# 5. Get the root logger and add the new handlers

root_logger = logging.getLogger()
root_logger.addHandler(general_file_handler)
root_logger.addHandler(console_handler) # הוסף גם את handler הקונסול
root_logger.setLevel(logging.INFO) # הגדר את רמת הלוג המינימלית ל-INFO

# Create specific loggers for each log type
# ... (Rest of the code for specific logger definitions) ...


# Create specific loggers for each log type
# We'll define them as a single instance so they are easily available for import.
# These will be the loggers we use to send the different metrics.
scraper_events_logger = setup_file_logger(
    "scraper.events", "scraper_events.log", level=logging.INFO
    ) # For per-currency/exchange events
scraper_run_summary_logger = setup_file_logger(
    "scraper.run_summary", "scraper_run_summary.log", level=logging.INFO
    ) # For full run summary
exchange_scrape_report_logger = setup_file_logger(
    "scraper.exchange_report", "exchange_scrape_report.log", level=logging.INFO
    ) # For per-exchange summary
scraper_resource_logger = setup_file_logger(
    "scraper.resources", "scraper_resources.log", level=logging.INFO
    ) # For resource metrics
db_heartbeat_logger = setup_file_logger(
    "db_worker.heartbeat", "db_heartbeat.log", level=logging.INFO
)
db_flush_events_logger = setup_file_logger(
    "db_worker.flush_events", "db_flush_events.log", level=logging.INFO
)

# --- 2. Helper function for sending metrics/logs ---

def send_metric_log(model_instance: BaseMonitoringEvent): 
    """
    Helper function for sending structured logs/metrics.
    Receives an instance of a Pydantic model (which inherits from BaseMonitoringEvent).
    The function selects the appropriate logger and sends the data.
    """
    if isinstance(model_instance, ScraperRunSummary):
        logger_instance = scraper_run_summary_logger
    elif isinstance(model_instance, ExchangeScrapeReport):
        logger_instance = exchange_scrape_report_logger
    elif isinstance(model_instance, ExchangeCurrencyEvent):
        logger_instance = scraper_events_logger
    elif isinstance(model_instance, ScraperProcessResourceMetric):
        logger_instance = scraper_resource_logger
    elif isinstance(model_instance, DBWorkerHeartbeatEvent):
        logger_instance = db_heartbeat_logger
    elif isinstance(model_instance, DBWorkerBatchFlushEvent):
        logger_instance = db_flush_events_logger
    else:
        # Log an error if an unknown model is received
        structlog.get_logger("monitoring.utils").error(
            "Attempted to send metric with unknown model type",
            model_type=type(model_instance).__name__,
            data=model_instance.model_dump(mode='json')
        )
        return

    
    # Pydantic's .model_dump() converts the object to a Python dictionary.
    # structlog will handle the rest of the additions (like timestamp, host_id) and JSON rendering.
    logger_instance.info("Monitoring Event", **model_instance.model_dump(mode='json'))
    # logger_instance.handlers[0].flush()


# --- 3. Asynchronous decorators for monitoring ---
def time_async_function(component_name: str, event_name: str):
    """
    Decorator for measuring coroutine execution time and sending an ExchangeCurrencyEvent metric.
    If the wrapped function returns a ScraperRunSummary, the metric will be sent specifically for it.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = None
            try:
                result = await func(*args, **kwargs)
            finally:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000

                if isinstance(result, ScraperRunSummary):
                    result.total_run_duration_ms = duration_ms
                    send_metric_log(result)
                elif isinstance(result, ExchangeScrapeReport): # Also add handling for ExchangeScrapeReport
                    # If this is the main exchange function returning its report,
                    # will be handled in the overall ScraperRunSummary.
                    # For now, we'll omit duration_ms from ExchangeScrapeReport if it's not present there.
                    send_metric_log(result)
                else:
                    send_metric_log(
                        ExchangeCurrencyEvent(
                            component_name=component_name,
                            currency_pair=kwargs.get('currency_pair', 'N/A'), 
                            event_name=event_name,
                            duration_ms=duration_ms
                        )
                    )
            return result # Return the original result of the function
        return wrapper
    return decorator


def handle_async_errors(component_name: str, is_critical: bool = False):
    """
    Decorator for handling and sending errors from a coroutine as an ExchangeCurrencyEvent.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_details = ErrorDetails(
                    error_code=type(e).__name__,
                    error_message=str(e),
                    is_critical=is_critical,
                    stack_trace=None # structlog.processors.format_exc_info will handle this
                )

                # Send an error log with the model details
                # structlog will automatically add exc_info if it's in PROCESSORS
                send_metric_log(
                    ExchangeCurrencyEvent(
                        component_name=component_name,
                        currency_pair=kwargs.get('currency_pair', 'N/A'), # If relevant
                        event_name=f"{func.__name__}_failed",
                        error_details=error_details
                    )
                )
                # raise # Important to re-raise the error if it's not fully handled at this level.
        return wrapper
    return decorator


# --- 4. Function for collecting and sending resource metrics (scraper) ---
# We will use this only when we implement resource monitoring.
async def start_scraper_resource_monitoring(pid: int,interval_seconds: int = 10):
    """
    Starts an asynchronous task for monitoring scraper process resources.
    """
    # ... (This code will be implemented when I figure out how to implement resource monitoring) ...
    # For now, we'll put a placeholder here so it doesn't break the file
    scraper_resource_logger.info("Resource monitoring function placeholder called for pid", pid=pid)
    await asyncio.sleep(0.1) # To allow the asynchronous loop to continue


async def send_heartbeat(redis_client: redis.Redis,data_buffer: dict,last_flush_time:dict, interval_seconds: int = 60,logger: structlog.stdlib.BoundLogger =db_heartbeat_logger):
    """
    Periodically sends a DBWorkerHeartbeatEvent to confirm the worker's operational status.
    """
    logger.info(f"DB Worker Heartbeat task started (interval: {interval_seconds}s).")
    while True:
        await asyncio.sleep(interval_seconds) # Wait for the specified interval
        
        total_buffered_items = sum(len(lst) for lst in data_buffer.values())
        current_queue_length = -1 # Default to -1 in case of Redis connection issues
        redis_error_details = None
        try:
            # Attempt to get Redis queue length
            current_queue_length = await redis_client.llen("order_book_updates")
        except Exception as e:
            logger.info(f"Warning: Could not get Redis queue length for heartbeat: {e}")
            redis_error_details = ErrorDetails(
                error_code=type(e).__name__,
                error_message=f"Failed to get Redis queue length: {str(e)}",
                is_critical=False
            )
        
        status = "alive"
        if redis_error_details:
             status = "degraded" # Example: mark as degraded if Redis queue length fails

        # Send the heartbeat metric
        model_instance = DBWorkerHeartbeatEvent(
                status=status, # You could add more sophisticated logic for "healthy" or "degraded"
                current_queue_length=current_queue_length,
                buffered_items_count=total_buffered_items,
                last_flush_time_global=max(last_flush_time.values(), default=None) if last_flush_time else None,
                error_details=redis_error_details
            )
        send_metric_log(model_instance)
        logger.info("DB Worker Heartbeat sent.")
