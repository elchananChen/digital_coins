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
import structlog
import psutil
import uuid
import copy

from utils.util_functions import add_overall_exchange_status,merge_addition_dicts

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

# ---  Process Resource Metrics Collection ---
def get_process_resource_metrics(process: psutil.Process, run_id: str, logger:structlog.stdlib.BoundLogger) -> ScraperProcessResourceMetric:
    """
    Collects resource metrics for a given process and returns a ScraperProcessResourceMetric model.
    """
    try:
        cpu_percent = process.cpu_percent(interval=None)
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        open_fds = process.num_fds()
        threads_count = process.num_threads()

        browser_cpu_percent = None
        browser_memory_mb = None

        # Try to find Playwright browser process if available
        # This part might need refinement based on how Playwright child processes are identifiable
        for p in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
            try:
                p_name = p.info['name'].lower()
                if 'chrome' in p_name or 'chromium' in p_name or 'msedge' in p_name:
                    browser_cpu_percent = p.cpu_percent(interval=None)
                    browser_memory_mb = p.memory_info().rss / (1024 * 1024)
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                continue
        return ScraperProcessResourceMetric(
            process_id=process.pid,
            process_name=process.name(),
            cpu_usage_percent=cpu_percent,
            memory_usage_mb=memory_mb,
            open_file_descriptors=open_fds,
            threads_count=threads_count,
            browser_process_cpu_percent=browser_cpu_percent,
            browser_process_memory_mb=browser_memory_mb,
            run_id=run_id,
        )
    except psutil.NoSuchProcess:
        logger.warning("Attempted to get metrics for a non-existent process.", run_id=run_id, process_id=process.pid)
        return None
    except Exception as e:
        logger.error("Failed to collect process resource metrics", exception=e, run_id=run_id, exc_info=True)
        return None

async def monitoring_loop(run_id: str,current_process,logger:structlog.stdlib.BoundLogger, interval_sec: int = 30,): 
    """
    Sends periodic process resource metrics.
    """
    logger.info("Starting process resource monitoring loop")
    while True:
        try:
            # --- Send Process Resource Metrics ---
            resource_metrics = get_process_resource_metrics(process=current_process, run_id=run_id,logger=logger)
            if resource_metrics:
                send_metric_log(resource_metrics)
            logger.info(f"Process resource metrics sent (run id: {run_id})")

        except Exception as e:
            logger.error(f"Error in process resource monitoring loop \n Exception: {e}")
        finally:
            await asyncio.sleep(interval_sec)


def add_run_summery_status(exchange_status,run_summery_status_dict):
    if exchange_status == "success":
        run_summery_status_dict["fully_successful_exchange_scrapes"] += 1
    elif exchange_status == "success_with_errors":
        run_summery_status_dict["fully_successful_with_errors_exchange_scrapes"] += 1
    elif exchange_status == "partial":
        run_summery_status_dict["partial_success_exchange_scrapes"] += 1
    elif exchange_status == "failed":
        run_summery_status_dict["fully_failed_exchange_scrapes"] += 1

async def generate_and_log_scrape_summaries(exchange_metrics: dict, interval_delay,logger:structlog.stdlib.BoundLogger) -> None:
    logger.info("generate_and_log_scrape_summaries started")
    while True:
        try:
            start = time.perf_counter()
            await asyncio.sleep(interval_delay)
            # logger.info(exchange_metrics)
            # Make copy 
            metrics_snapshot = copy.deepcopy(exchange_metrics)

            # Reset the global EXCHANGE_METRICS (he continue to collect data)
            run_id = uuid.uuid4()
            for exchange_name in exchange_metrics:
                if exchange_name.startswith("_"):
                    continue
                exchange_metrics[exchange_name]["run_id"] = run_id 
                exchange_metrics[exchange_name]["active_currency_pairs"] = set()
                exchange_metrics[exchange_name]["total_currency_pairs_configured"] = len(exchange_metrics[exchange_name]["currency_metrics"])
                exchange_metrics[exchange_name]["successful_currency_pair_initializations"] = 0
                exchange_metrics[exchange_name]["failed_currency_pair_initializations"] = 0
                exchange_metrics[exchange_name]["total_data_points_sent_to_redis"] = 0
                exchange_metrics[exchange_name]["errors_summary"] = {}
                exchange_metrics[exchange_name]["overall_exchange_status"] = ""
                for currency_name, currency_data in exchange_metrics[exchange_name]["currency_metrics"].items():
                        currency_data["data_point_id"] = str(uuid.uuid4())
                        currency_data["latency_avg_ms"] = 0.0
                        currency_data["points_send_to_redis"] = 0
                        currency_data["duration_ms"]= 0
                        currency_data["error_details"] = {}
                        currency_data["status"] = "failed"
                        currency_data["avg_volume_count"] = 0

            exchange_metrics["_run_id"] = run_id

            if not metrics_snapshot:
                logger.critical("EXCHANGE_METRICS dict is empty")
                continue
            
            session_run_id = metrics_snapshot["_run_id"]

            total_exchanges_configured = len(metrics_snapshot) - 1

            run_summery_status = {
                "fully_successful_exchange_scrapes": 0,
                "fully_successful_with_errors_exchange_scrapes": 0,
                "partial_success_exchange_scrapes": 0,
                "fully_failed_exchange_scrapes": 0,
                }

            total_currency_pairs_configured = 0

            successful_currency_pair_initializations = 0
            failed_currency_pair_initializations = 0
            total_data_points_sent_to_redis = 0
            aggregated_errors_summary = {}

            # run on all exchanges 
            for exchange_name, exchange_data in metrics_snapshot.items():

                if exchange_name.startswith("_"):
                    continue

                # run on all currencies and add data to exchange summery and currency summery
                # log currency summery
                for currency_name, currency_data in exchange_data["currency_metrics"].items():
                    if currency_data["points_send_to_redis"] > 0:
                        exchange_data["successful_currency_pair_initializations"] +=  1
                        exchange_data["total_data_points_sent_to_redis"] += currency_data["points_send_to_redis"]
                        currency_data["status"] = "success"
                    else:
                        exchange_data["failed_currency_pair_initializations"] +=1
                        currency_data["status"] = "failed"

                    exchange_data["errors_summary"] = merge_addition_dicts(
                        exchange_data["errors_summary"],
                        currency_data["error_details"]
                        )

                    # send ExchangeCurrencyEvent
                    send_metric_log(ExchangeCurrencyEvent(
                        run_id = str(session_run_id),
                        component_name = exchange_name,
                        currency_pair = currency_name,
                        event_name = "currency_summery",
                        data_point_id = str(currency_data["data_point_id"]),
                        initial_latency_ms = currency_data["initial_latency_ms"],
                        latency_avg_ms = currency_data["latency_avg_ms"],
                        points_send_to_redis = currency_data["points_send_to_redis"],
                        error_details = currency_data["error_details"],
                        status = currency_data["status"],
                    ))
                
                aggregated_errors_summary = merge_addition_dicts(
                aggregated_errors_summary,
                exchange_data["errors_summary"]
                )

                add_overall_exchange_status(monitor_data=exchange_data)

                status = exchange_data.get("overall_exchange_status", "").lower()
                
                # collect run summery data
                add_run_summery_status(exchange_status=status,run_summery_status_dict=run_summery_status)
                total_currency_pairs_configured += exchange_data["total_currency_pairs_configured"]
                successful_currency_pair_initializations += exchange_data["successful_currency_pair_initializations"]
                failed_currency_pair_initializations += exchange_data["failed_currency_pair_initializations"]
                total_data_points_sent_to_redis += exchange_data["total_data_points_sent_to_redis"]


                # send ExchangeScrapeReport
                send_metric_log(
                    ExchangeScrapeReport(
                        run_id=str(session_run_id),
                        exchange_name=exchange_name,
                        total_currency_pairs_configured=exchange_data["total_currency_pairs_configured"],
                        successful_currency_pair_initializations=exchange_data["successful_currency_pair_initializations"],
                        failed_currency_pair_initializations=exchange_data["failed_currency_pair_initializations"],
                        total_data_points_sent_to_redis=exchange_data["total_data_points_sent_to_redis"],
                        errors_summary=exchange_data["errors_summary"],
                        overall_exchange_status=status,
                ))

            end = time.perf_counter()
            total_run_duration_ms = (end - start) * 1000

            # send ScraperRunSummary
            send_metric_log(
                ScraperRunSummary(
                    run_id=str(session_run_id),
                    total_run_duration_ms=total_run_duration_ms,
                    total_exchanges_configured=total_exchanges_configured,
                    fully_successful_exchange_scrapes=run_summery_status["fully_successful_exchange_scrapes"],
                    fully_successful_with_errors_exchange_scrapes=run_summery_status["fully_successful_with_errors_exchange_scrapes"],
                    partial_success_exchange_scrapes=run_summery_status["partial_success_exchange_scrapes"],
                    fully_failed_exchange_scrapes=run_summery_status["fully_failed_exchange_scrapes"],
                    total_currency_pairs_configured=total_currency_pairs_configured,
                    successful_currency_pair_initializations=successful_currency_pair_initializations,
                    failed_currency_pair_initializations=failed_currency_pair_initializations,
                    total_data_points_sent_to_redis=total_data_points_sent_to_redis,
                    errors_summary=aggregated_errors_summary
            ))

        except Exception as e:
            logger.exception("Error during generate_and_log_scrape_summaries", exc_info=e)    

def get_or_create_currency_metrics(exchange_metrics: dict, db_symbol: str, currency_id: str):
    if db_symbol not in exchange_metrics["currency_metrics"]:
        exchange_metrics["currency_metrics"][db_symbol] = {
            "currency_pair": db_symbol,
            "data_point_id": str(currency_id),
            "initial_latency_ms":0,
            "latency_avg_ms":0.0,
            "points_send_to_redis":0,
            "duration_ms":0,
            "error_details":{},
            "status":"failed",
            "avg_volume_count": 0,
        }

    return exchange_metrics["currency_metrics"][db_symbol]

def update_latency_avg(metrics: dict, current_latency_ms: float):
    count = metrics.get("avg_volume_count", 0)
    avg = metrics.get("latency_avg_ms", 0)

    new_sum = avg * count + current_latency_ms
    new_count = count + 1

    metrics["latency_avg_ms"] = new_sum / new_count
    metrics["avg_volume_count"] = new_count
