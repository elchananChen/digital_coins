import uuid
from lists.bit_stamp_lists import bit_stamp_symbols


run_id = uuid.uuid4()
EXCHANGES_METRICS = {
    "_run_id": run_id,
    "bitStamp": {
       "run_id": run_id,
       "exchange_name": "bitStamp",
       "overall_exchange_status": "",
       "active_currency_pairs": set(),
       "total_currency_pairs_configured": len(bit_stamp_symbols),
       "currency_pair_initialized": 0,
       "successful_currency_pair_initializations":0,
       "failed_currency_pair_initializations":0,
       "total_data_points_sent_to_redis": 0,
       "errors_summary":{},
       "currency_metrics": {},
    },
}
