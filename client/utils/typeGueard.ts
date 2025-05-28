import { TUsdtSymbol, usdtSymbols } from '@/types/OrderBookTypes';

export const usdtTypeGuard = (symbol: any): symbol is TUsdtSymbol => {
  return typeof symbol === 'string' && usdtSymbols.includes(symbol as TUsdtSymbol);
};
