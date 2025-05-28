export type TUsdSymbol =
  | 'BTCUSD' // Bitcoin
  | 'ETHUSD' // Ethereum
  | 'LTCUSD' // Litecoin
  | 'XRPUSD' // Ripple (XRP)
  | 'BCHUSD'; // Bitcoin Cash

export const usdtSymbols = [
  'BTCUSDT', // Bitcoin
  'ETHUSDT', // Ethereum
  'LTCUSDT', // Litecoin
  'XRPUSDT', // Ripple (XRP)
  'BCHUSDT', // Bitcoin Cash
] as const;

export type TUsdtSymbol = (typeof usdtSymbols)[number];

export type TPriceAmount = {
  price: number;
  amount: number;
};

export type TOrderBookRes = {
  exchange: 'coinbase' | 'bitstamp' | 'kraken' | 'binance';
  symbol: TUsdSymbol | TUsdtSymbol;
  timestamp: Date;
  bids: TPriceAmount[];
  asks: TPriceAmount[];
};
