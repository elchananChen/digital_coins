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
    # safety checks
    if  "total_currency_pairs_configured" in monitor_data\
        and isinstance(monitor_data["total_currency_pairs_configured"],int)\
        and "failed_currency_pair_initializations" in monitor_data \
        and isinstance(monitor_data["failed_currency_pair_initializations"],int)\
        and "errors_summary" in monitor_data \
        and isinstance(monitor_data["errors_summary"],dict):

        failures = monitor_data["failed_currency_pair_initializations"]
        total_currencies = monitor_data["total_currency_pairs_configured"]
        # get the errors_sum 
        errors_sum = 0
        for error_value in monitor_data["errors_summary"].values(): 
            if isinstance(error_value, int):
                errors_sum += error_value

        # status logic
        if errors_sum == 0 and failures == 0:
            monitor_data["status"] = "fully_successful" 
        elif errors_sum > 0 and failures == 0:
            monitor_data["status"] = "fully_successful_with_errors"
        elif failures < total_currencies:
            monitor_data["status"] = "partial_success"
        elif failures == total_currencies:
            monitor_data["status"] = "fully_failed"


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
    fully_successful_exchange_scrapes_count = 0
    fully_successful_with_errors_exchange_scrapes_count = 0
    partial_success_exchange_scrapes_count = 0
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
            if result.overall_exchange_status == "fully_successful":
                fully_successful_exchange_scrapes_count += 1
            elif result.overall_exchange_status == "fully_successful_with_errors":
                fully_successful_with_errors_exchange_scrapes_count += 1
            elif result.overall_exchange_status == "partial_success":
                partial_success_exchange_scrapes_count += 1
            elif result.overall_exchange_status == "fully_failed":
                fully_failed_exchange_scrapes_count += 1

            # Sum up currency pair and data point metrics
            total_currency_pairs_configured_overall += result.total_currency_pairs_configured
            successful_currency_pair_initializations_overall += result.successful_currency_pair_initializations
            failed_currency_pair_initializations_overall += result.failed_currency_pair_initializations
            total_data_points_sent_across_all_exchanges += result.total_data_points_sent_to_redis

            # Merge errors
            overall_errors_summary.update(result.errors_summary)

        elif isinstance(result, Exception):
            # This indicates a critical failure where the scraper task itself crashed
            fully_failed_exchange_scrapes_count += 1
            logger.critical(f"🔥 CRITICAL: An exchange scraper task crashed due to unhandled exception: {type(result).__name__}: {result}")
            overall_errors_summary.update({"system_level_task_crash": 1})
            # You might want to get the name of the exchange that crashed if possible
            # (requires passing exchange_name to the exception handling in main's gather loop)


    # Create and return the ScraperRunSummary object
    run_summary_data = {
        "run_id": run_id, 
        "close_status": close_status, # This needs to be set based on main's final status
        "total_run_duration_ms": 0.0, # This needs to be set in main's decorator or finally block

        # Exchange-level Metrics
        "total_exchanges_configured": total_exchanges_configured,
        "fully_successful_exchange_scrapes": fully_successful_exchange_scrapes_count,
        "fully_successful_with_errors_exchange_scrapes": fully_successful_with_errors_exchange_scrapes_count,
        "partial_success_exchange_scrapes": partial_success_exchange_scrapes_count,
        "fully_failed_exchange_scrapes": fully_failed_exchange_scrapes_count,

        # Currency Pair-level Metrics
        "total_currency_pairs_configured": total_currency_pairs_configured_overall,
        "successful_currency_pair_initializations": successful_currency_pair_initializations_overall,
        "failed_currency_pair_initializations": failed_currency_pair_initializations_overall,

        # Data Volume and Quality Metrics
        "total_data_points_sent_to_redis": total_data_points_sent_across_all_exchanges,
        "errors_summary": dict(overall_errors_summary) # Convert Counter to dict for Pydantic model
    }
    
    # You might consider passing the run_id and total_run_duration_ms to this function,
    # or setting them on the returned object in the main function.
    
    # Returning a dict here, and letting main() create the ScraperRunSummary object
    # is often cleaner, as run_id and duration are properties of the main run, not just aggregation.
    
    return run_summary_data