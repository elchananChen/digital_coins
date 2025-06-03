import { TExchangeName } from '@/shared/constants/exchanges';

export const usdSymbols = [
  'BTCUSD', // Bitcoin
  'ETHUSD', // Ethereum
  'LTCUSD', // Litecoin
  'XRPUSD', // Ripple (XRP)
  'BCHUSD', // Bitcoin Cash
] as const;

export const usdtSymbols = [
  'BTCUSDT', // Bitcoin
  'ETHUSDT', // Ethereum
  'LTCUSDT', // Litecoin
  'XRPUSDT', // Ripple (XRP)
  'BCHUSDT', // Bitcoin Cash
] as const;

export type TUsdtSymbol = (typeof usdtSymbols)[number];
export type TUsdSymbol = (typeof usdSymbols)[number];

export type TPriceAmount = {
  price: number;
  amount: number;
};

export type TOrderBookRes = {
  exchange: TExchangeName;
  symbol: TUsdSymbol | TUsdtSymbol;
  timestamp: Date;
  bids: TPriceAmount[];
  asks: TPriceAmount[];
};

export type TCurrency = 'usdt' | 'usd';
