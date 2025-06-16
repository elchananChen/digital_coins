from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

# --- Base Model for all Monitoring Events ---
class BaseMonitoringEvent(BaseModel):
    """
    מודל בסיס לכל אירועי הניטור, כולל שדות משותפים.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow) # חותמת זמן UTC
    service_name: str
    host_id: str = Field(default_factory=lambda: "unknown_host") # ברירת מחדל, תעודכן ע"י structlog או קוד
    metric_type: str

# --- 1. מדדים כלליים של ריצת Scraper (Run Summary) ---
class ScraperRunSummary(BaseMonitoringEvent):
    """
    מודל עבור סיכום ריצה מלאה של הסקריפר.
    """
    run_id: str
    total_run_duration_ms: float
    total_exchanges_configured: int
    successful_exchange_scrapes: int
    failed_exchange_scrapes: int
    total_currency_pairs_scraped: int
    data_points_sent_to_redis_total: int
    errors_summary: Dict[str, int] = Field(default_factory=dict) # מילון של סוג שגיאה וכמותה

    def __init__(self, **data: Any):
        super().__init__(service_name="scraper", metric_type="run_summary", **data)

# --- 2. (Exchange & Currency Specific Metrics) ---
class ErrorDetails(BaseModel):
    """
    מודל עזר לפרטי שגיאה.
    """
    error_code: str
    error_message: str
    is_critical: bool = False
    retry_attempts: Optional[int] = None
    stack_trace: Optional[str] = None # אופציונלי, יתווסף ע"י structlog ExcInfoRenderer

class ExchangeCurrencyEvent(BaseMonitoringEvent):
    """
    מודל עבור אירועים ספציפיים למטבע/בורסה.
    """
    component_name: str # שם הבורסה (לדוגמה, "binance_scraper")
    currency_pair: str  # זוג המטבעות (לדוגמה, "ETH/USD")
    event_name: str     # סוג האירוע: data_sent_to_redis, page_load_success, etc.
    data_point_id: Optional[str] = None # מזהה ייחודי לנקודת נתונים
    duration_ms: Optional[float] = None
    data_volume_bytes: Optional[int] = None
    latency_since_last_save_ms: Optional[float] = None
    current_redis_queue_length: Optional[int] = None
    error_details: Optional[ErrorDetails] = None
    browser_tab_id: Optional[str] = None
    current_open_tabs_count: Optional[int] = None

    def __init__(self, **data: Any):
        super().__init__(service_name="scraper", metric_type="exchange_currency_event", **data)


# --- 3. Scraper (Scraper Process Resources) ---
class ScraperProcessResourceMetric(BaseMonitoringEvent):
    """
    מודל עבור מדדי משאבים של תהליך הסקריפר.
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