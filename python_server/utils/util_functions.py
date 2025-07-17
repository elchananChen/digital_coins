import logging
import uuid
from collections import Counter
from monitoring.models import ScraperRunSummary, ExchangeScrapeReport, CloseStatusEnum # וודא שאתה מייבא הכל
from typing import List, Union, Dict, Any
logger = logging.getLogger(__name__)

def merge_addition_dicts(dict1:dict,dict2:dict):
    counter1 = Counter(dict1)
    counter2 = Counter(dict2)
    return dict(counter1 + counter2)


def add_overall_exchange_status(monitor_data:dict ):
        failures = monitor_data["failed_currency_pair_initializations"]
        total_currencies = monitor_data["currency_pair_initialized"]

        # get the errors_sum
        errors_sum = 0
        for error_value in monitor_data["errors_summary"].values(): 
            if isinstance(error_value, int):
                errors_sum += error_value
        logger.warning(f"errors_sum {errors_sum}")
        logger.warning(f"failures {failures}")
        logger.warning(f"total_currencies {total_currencies}")

        # status logic
        if errors_sum == 0 and failures == 0:
            monitor_data["overall_exchange_status"] = "success" 
        elif errors_sum > 0 and failures == 0:
            monitor_data["overall_exchange_status"] = "success_with_errors"
        elif failures < total_currencies:
            monitor_data["overall_exchange_status"] = "partial"
        elif failures == total_currencies:
            monitor_data["overall_exchange_status"] = "failed"


async def aggregate_scraper_results(
        all_exchange_results: List[Union[ExchangeScrapeReport, Exception]],
        total_exchanges_configured: int,
        close_status: CloseStatusEnum,
        run_id: str
        ) -> ScraperRunSummary:
    
    """
    Aggregates results from individual exchange scrapers into a comprehensive system-wide report,
    then populates and returns a ScraperRunSummary object.
    """

    # Initialize aggregated counters and data structures
    total_exchanges_configured = total_exchanges_configured
    fully_failed_exchange_scrapes_count = 0 # This will also include tasks that returned an Exception

    total_currency_pairs_configured_overall = 0
    successful_currency_pair_initializations_overall = 0
    failed_currency_pair_initializations_overall = 0
    total_data_points_sent_across_all_exchanges = 0
    overall_errors_summary = Counter() # Using Counter for easy merging

    # Optional: to store each detailed exchange report within the summary (useful for debugging)
    exchange_specific_reports: Dict[str, Dict[str, Any]] = {} 

    for result in all_exchange_results:
        if isinstance(result, ExchangeScrapeReport):
            # Store the full report for detailed inspection if needed
            exchange_specific_reports[result.exchange_name] = result.model_dump() # Convert Pydantic model to dict

            # Aggregate exchange-level statuses
           
            # Sum up currency pair and data point metrics
            total_currency_pairs_configured_overall += result.total_currency_pairs_configured
            successful_currency_pair_initializations_overall += result.successful_currency_pair_initializations
            failed_currency_pair_initializations_overall += result.failed_currency_pair_initializations
            total_data_points_sent_across_all_exchanges += result.total_data_points_sent_to_redis

            # Merge errors
            overall_errors_summary.update(result.errors_summary)

        elif isinstance(result, Exception):
            print(f"ERROR: Unexpected result type in aggregate_scraper_results! Result: {result}, Type: {type(result)}")
            # This indicates a critical failure where the scraper task itself crashed
            fully_failed_exchange_scrapes_count += 1
            logger.critical(f"🔥 CRITICAL: An exchange scraper task crashed due to unhandled exception: {type(result).__name__}: {result}")
            overall_errors_summary.update({"system_level_task_crash": 1})
