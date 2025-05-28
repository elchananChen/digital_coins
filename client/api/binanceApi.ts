import { TOrderBookRes, TUsdSymbol, TUsdtSymbol } from '@/types/OrderBookTypes';
import { usdtTypeGuard } from '@/utils/typeGueard';
const BINANCE_URL = process.env.BINANCE_URL;
export const fetchBinanceOrderBook = async (symbol: TUsdtSymbol | TUsdSymbol) => {
  try {
    if (!usdtTypeGuard(symbol)) throw 'not a valid symbol for Binance';
    const params = new URLSearchParams({ symbol });
    const response = await fetch(`${BINANCE_URL}/book_order?${params.toString()}`);
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
