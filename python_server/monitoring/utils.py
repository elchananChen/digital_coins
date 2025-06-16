# monitors/utils.py
import logging
import json
import time
import asyncio
import functools
import os
import socket
import sys
import structlog
import psutil

# ייבוא מבני ה-JSON שהגדרנו ב-models.py
from monitoring.models import (
    BaseModel, # חשוב לייבא את BaseModel כדי לטפל במופעים של Pydantic
    ScraperRunSummary,
    ExchangeCurrencyEvent,
    ScraperProcessResourceMetric,
    ErrorDetails # גם את זה נצטרך בתוך הדקורטור לטיפול בשגיאות
)

# --- 1. define structlog  (and logging ) basic definition ---
'''
 Set up logging in its simplest form,
 allowing structlog to control the log formatting
'''

logging.basicConfig(
    format="%(message)s", # structlog יטפל בפורמט הסופי
    stream=sys.stdout, # או sys.stderr, או קובץ לוג, תלוי בתצורה הסופית
    level=logging.INFO, # רמת הלוג מינימלית
)

# פונקציית עזר להוספת host_id גלובלי לכל לוג (Processor)
def add_host_id(logger, method_name, event_dict):
    """Adds the hostname to the event dict."""
    event_dict["host_id"] = socket.gethostname()
    return event_dict

# מעבדי structlog גלובליים
# מעבדים אלה ירוצו עבור כל לוג שיופק דרך structlog
PROCESSORS = [
    structlog.stdlib.add_logger_name,  # מוסיף את שם הלוגר
    structlog.stdlib.add_log_level,    # מוסיף את רמת הלוג (INFO, ERROR וכו')
    structlog.processors.TimeStamper(fmt="iso", utc=True), # מוסיף חותמת זמן בפורמט ISO ב-UTC
    add_host_id, # מעבד מותאם אישית להוספת Host ID
    structlog.processors.StackInfoRenderer(), # מוסיף stack info עבור שגיאות
    structlog.processors.format_exc_info, # מוסיף מידע אודות אקצפשנים ללוג
    structlog.dev.ConsoleRenderer() if os.environ.get("ENV") == "development" else structlog.processors.JSONRenderer(), # מרינדר כ-JSON בפרודקשן, כקונסול בפיתוח
]

structlog.configure(
    processors=PROCESSORS,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# יצירת לוגרים ספציפיים לכל סוג לוג
# נגדיר אותם כמופע יחיד כדי שיהיו זמינים בקלות לייבוא.
# אלו יהיו הלוגרים שנשתמש בהם כדי לשלוח את המדדים השונים.
scraper_events_logger = structlog.get_logger("scraper.events") # לאירועים פר מטבע/בורסה
scraper_run_summary_logger = structlog.get_logger("scraper.run_summary") # לסיכום ריצה
scraper_resource_logger = structlog.get_logger("scraper.resources") # למדדי משאבים


# --- 2. פונקציית עזר לשליחת מדדים/לוגים ---
def send_metric_log(logger_instance: structlog.stdlib.BoundLogger, model_instance: BaseModel):
    """
    פונקציית עזר לשליחת לוגים/מדדים מובנים.
    מקבלת מופע לוגר ומופע של מודל Pydantic.
    """
    # Pydantic's .model_dump() ממיר את האובייקט למילון פייתון.
    # structlog יטפל ביתר התוספות (כמו timestamp, host_id) והרינדור ל-JSON.
    logger_instance.info("Monitoring Event", **model_instance.model_dump(mode='json'))

# --- 3. דקורטורים אסינכרוניים לניטור ---

def time_async_function(component_name: str, event_name: str, logger_instance: structlog.stdlib.BoundLogger):
    """
    דקורטור למדידת זמן ריצה של קורוטינה ושליחת מדד.
    הדקורטור מצפה שהפונקציה העטופה תחזיר אובייקט Pydantic שלם (כמו ScraperRunSummary)
    אם היא הפונקציה הראשית, או יעבוד עם ExchangeCurrencyEvent אחרת.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = None
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000

                if isinstance(result, ScraperRunSummary):
                    # אם הפונקציה החזירה ScraperRunSummary, נעדכן את השדה duration_ms שלו
                    # ונשלח אותו.
                    result.total_run_duration_ms = duration_ms
                    send_metric_log(logger_instance, result)
                else:
                    # אחרת, נשלח מדד רגיל של ExchangeCurrencyEvent
                    # (זהו תרחיש עבור מדידת פונקציות פנימיות יותר)
                    send_metric_log(
                        logger_instance,
                        ExchangeCurrencyEvent(
                            component_name=component_name,
                            currency_pair=kwargs.get('currency_pair', 'N/A'), # נניח ש-currency_pair נמצא ב-kwargs
                            event_name=event_name,
                            duration_ms=duration_ms
                        )
                    )
        return wrapper
    return decorator


def handle_async_errors(component_name: str, logger_instance: structlog.stdlib.BoundLogger, is_critical: bool = False):
    """
    דקורטור לטיפול ושליחת שגיאות מקורוטינה.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # יצירת מופע של ErrorDetails
                error_details = ErrorDetails(
                    error_code=type(e).__name__,
                    error_message=str(e),
                    is_critical=is_critical,
                    stack_trace=None # structlog.processors.format_exc_info יטפל בזה
                )
                
                # שליחת לוג שגיאה עם פרטי המודל
                # structlog יוסיף את ה-exc_info באופן אוטומטי אם הוא ב-PROCESSORS
                logger_instance.error(
                    f"Error in {func.__name__}",
                    component_name=component_name,
                    currency_pair=kwargs.get('currency_pair', 'N/A'), # אם רלוונטי
                    event_name=f"{func.__name__}_failed",
                    error_details=error_details.model_dump(mode='json'), # ממיר את מודל השגיאה למילון
                    exc_info=True # חשוב מאוד כדי ש-structlog יכלול stack trace מלא
                )
                raise # חשוב להעביר את השגיאה הלאה אם היא לא מטופלת באופן מלא ברמה זו.
        return wrapper
    return decorator


# --- 4. פונקציה לאיסוף ושליחת מדדי משאבים (סקריפר) ---
# נשתמש בזה רק כשניישם את ניטור המשאבים.
async def start_scraper_resource_monitoring(pid: int, interval_seconds: int = 10):
    """
    מתחיל משימה אסינכרונית לניטור משאבי תהליך הסקריפר.
    """
    # ... (קוד זה ימומש כשאניידע איך ליישם את ניטור המשאבים) ...
    # לבינתיים, נשים פה placeholder כדי לא לשבור את הקובץ
    scraper_resource_logger.info("Resource monitoring function placeholder called for pid", pid=pid)
    await asyncio.sleep(0.1) # כדי לאפשר ללופ האסינכרוני להמשיך