import { TExchangeName } from '@/shared/constants/exchanges';
import { TCurrency, TOrderBookRes, TUsdSymbol, TUsdtSymbol } from '@/types/OrderBookTypes';
import { usdtTypeGuard, usdTypeGuard } from '@/utils/typeGueard';

const ORDER_BOOK_URL = process.env.ORDER_BOOK_URL;

export const fetchOrderBook = async (
  currency: TCurrency,
  symbol: TUsdtSymbol | TUsdSymbol,
  exchange: TExchangeName
) => {
  try {
    if (currency === 'usdt' && !usdtTypeGuard(symbol))
      throw `${symbol} is not a valid symbol for ${exchange}`;
    if (currency === 'usd' && !usdTypeGuard(symbol)) throw 'not a valid symbol for the exchange';

    const params = new URLSearchParams({ exchange, symbol });
    const response = await fetch(`${ORDER_BOOK_URL}?${params.toString()}`);

    // console.log(response);

    const data = await response.json();

    // console.log(data);
    // console.log('baba');

    if (!data || data.length === 0) {
      console.warn(`No data for coin list `);
      return undefined;
    }

    return data.data as TOrderBookRes;
  } catch (error) {
    console.error('Error fetching :', error);
    throw error;
  }
};
