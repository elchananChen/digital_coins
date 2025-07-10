from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

# --- Enums ---
class CloseStatusEnum(str, Enum):
    planned_shutdown = "planned shutdown"
    unplanned_shutdown = "unplanned shutdown"
    
# --- Base Model for all Monitoring Events ---
class BaseMonitoringEvent(BaseModel):
    """
    shared fields for all the monitoring event.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow) # חותמת זמן UTC
    service_name: str
    host_id: str = Field(default_factory=lambda: "unknown_host") # ברירת מחדל, תעודכן ע"י structlog או קוד
    metric_type: str

class ExchangeScrapeReport(BaseModel):
    """
    Pydantic model for a summary report of a single exchange's scraper run.
    """
    run_id: str
    exchange_name: str = Field(..., description="Name of the exchange (e.g., 'Bitstamp', 'Binance').")
    overall_exchange_status: str = Field(..., description="Overall status of this specific exchange's scrape (e.g., 'fully_successful', 'partial_success', 'fully_failed').")

    total_currency_pairs_configured: int = Field(..., description="Total currency pairs configured for this specific exchange.")
    successful_currency_pair_initializations: int = Field(..., description="Number of pairs that successfully started scraping for this exchange.")
    failed_currency_pair_initializations: int = Field(..., description="Number of pairs that failed for this specific exchange.")

    total_data_points_sent_to_redis: int = Field(..., description="Total data points sent by this exchange's scraper.")
    errors_summary: Dict[str, int] = Field(default_factory=dict, description="Summary of errors for this specific exchange.")

# --- Scraper (Run Summary) ---
class ScraperRunSummary(BaseMonitoringEvent):
    """
    Pydantic model for a comprehensive summary of a full scraper run.
    This model captures aggregated metrics across all exchanges.
    """

    run_id: str = Field(..., description="Unique ID for this specific scraper run instance.")
    close_status: CloseStatusEnum = Field(..., description="Overall status of the scraper's main process termination.")
    total_run_duration_ms: float = Field(..., description="Total duration of the entire scraper run in milliseconds.")

    # --- Exchange-level Metrics ---
    total_exchanges_configured: int = Field(..., description="Total number of exchanges configured to be scraped in this run.")
    fully_successful_exchange_scrapes: int = Field(..., description="")
    fully_successful_with_errors_exchange_scrapes: int = Field(..., description="")
    partial_success_exchange_scrapes: int = Field(..., description="")
    fully_failed_exchange_scrapes: int = Field(..., description="Number of exchanges whose individual scraper process terminated unexpectedly or with a critical error (i.e., returned an Exception object).")

    # --- Currency Pair-level Metrics ---
    total_currency_pairs_configured: int = Field(..., description="Total number of currency pairs configured across all exchanges for this run.")
    successful_currency_pair_initializations: int = Field(..., description="Number of currency pairs that successfully started scraping and sent at least one data point to Redis.")
    failed_currency_pair_initializations: int = Field(..., description="Number of currency pairs that failed to initialize or send any data points due to specific pair-level issues (e.g., specific errors for that pair).")

    # --- Data Volume and Quality Metrics ---
    total_data_points_sent_to_redis: int = Field(..., description="Total number of data points (e.g., order book snapshots) successfully sent to Redis by all scraper tasks combined.")
    errors_summary: Dict[str, int] = Field(default_factory=dict, description="A dictionary summarizing specific error types and their occurrence counts across all scraper tasks.")

    def __init__(self, **data: Any):
        super().__init__(service_name="scraper", metric_type="run_summary", **data)

# --- (Exchange & Currency Specific Metrics) ---
class ErrorDetails(BaseModel):
    error_code: str
    error_message: str
    is_critical: bool = False
    retry_attempts: Optional[int] = None
    # stack_trace: Optional[str] = None # optional, will add by structlog ExcInfoRenderer


class ExchangeCurrencyEvent(BaseMonitoringEvent):
    """
    for specific exchange/currency
    """
    run_id: Optional[str] = None
    component_name: str # exchange name (exc, "binance_scraper")
    currency_pair: str  # currency pair(exc, "ETH/USD")
    event_name: str     # event name: data_sent_to_redis, page_load_success, etc.
    data_point_id: Optional[str] = None
    duration_ms: Optional[float] = None
    latency_since_last_save_ms: Optional[float] = None
    initial_latency_ms: Optional[float] = None
    latency_avg_ms: Optional[float] = None
    points_send_to_redis: Optional[int] = None
    current_redis_queue_length: Optional[int] = None
    error_details: Dict[str, int] = Field(default_factory=dict, description="Summary of errors for this specific currency/exchanger pair.")
    status: Optional[str] = None

    def __init__(self, **data: Any):
        super().__init__(service_name="scraper", metric_type="exchange_currency_event", **data)


# --- Scraper (Scraper Process Resources) ---
class ScraperProcessResourceMetric(BaseMonitoringEvent):
    """
   for resources metrics (exc, cpu)
    """
    process_id: int
    process_name: str
    cpu_usage_percent: float
    memory_usage_mb: float
    open_file_descriptors: int
    threads_count: int
    browser_process_cpu_percent: Optional[float] = None
    browser_process_memory_mb: Optional[float] = None

    def __init__(self, **data: Any):
        super().__init__(service_name="scraper", metric_type="process_resource_metric", **data)


# ! ---------------  DB worker models -----------------


# ------ Heartbeat ------
class DBWorkerHeartbeatEvent(BaseMonitoringEvent):
    """
    Model for reporting the periodic heartbeat of the DB Worker.
    Confirms the worker is running and provides high-level status.
    """
    status: Literal["alive", "healthy", "degraded", "disconnected"] = Field(..., description="Current status of the DB Worker.")
    current_queue_length: Optional[int] = Field(None, description="Current length of the Redis queue (order_book_updates).")
    buffered_items_count: int = Field(..., description="Total number of items currently buffered across all keys, waiting to be flushed.")
    last_flush_time_global: Optional[datetime] = Field(None, description="Timestamp of the last global flush operation.")
    error_details: Optional[ErrorDetails] = Field(None, description="Details of any errors encountered during heartbeat collection (e.g., Redis connection issues).")

    def __init__(self, **data: Any):
        super().__init__(service_name="db_worker", metric_type="heartbeat", **data)


# ----- batch Flush ------
class DBWorkerBatchFlushEvent(BaseMonitoringEvent):
    """
    Model for reporting on each individual batch flush operation to MongoDB.
    Tracks performance, success/failure, and batch details.
    """
    event_type: Literal["batch_flush", "global_flush", "time_flush"] = Field(..., description="The type of flush event that triggered this write.")
    key: str = Field(..., description="The specific Redis key (e.g., 'symbol@exchange') that was flushed.")
    documents_count: int = Field(..., description="The number of documents inserted in this batch.")
    flush_duration_ms: float = Field(..., description="The time taken for the actual MongoDB insert operation in milliseconds.")
    status: Literal["success", "failure"] = Field(..., description="Whether the flush operation succeeded or failed.")
    error_details: Optional[ErrorDetails] = Field(None, description="Detailed error information if the flush failed.")
    buffer_size_before_flush: int = Field(..., description="The number of items in the buffer for this key just before the flush attempt.")

    def __init__(self, **data: Any):
        super().__init__(service_name="db_worker", metric_type="batch_flush", **data)

# ----- Queue event -----
class DBWorkerQueueEvent(BaseMonitoringEvent):
    """
    Model for logging events related to the Redis queue processing.
    Helps detect issues with message consumption or malformed data.
    """
    event_name: Literal["message_received", "malformed_message", "redis_connection_error", "general_processing_error", "data_validation_error"] = Field(..., description="Specific event type within queue processing.")
    queue_name: str = Field("order_book_updates", description="The name of the Redis queue being processed.")
    message_content_sample: Optional[str] = Field(None, description="A sample or snippet of the message content, especially for malformed messages.")
    error_details: Optional[ErrorDetails] = Field(None, description="Detailed error information if an error occurred during message processing.")

    def __init__(self, **data: Any):
        super().__init__(service_name="db_worker", metric_type="queue_event", **data)