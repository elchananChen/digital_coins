import { TUsdSymbol, TUsdtSymbol, usdSymbols, usdtSymbols } from '@/types/OrderBookTypes';

export const usdtTypeGuard = (symbol: any): symbol is TUsdtSymbol => {
  return typeof symbol === 'string' && usdtSymbols.includes(symbol as TUsdtSymbol);
};

export const usdTypeGuard = (symbol: any): symbol is TUsdSymbol => {
  return typeof symbol === 'string' && usdSymbols.includes(symbol as TUsdSymbol);
};
