export const EXCHANGES = {
  BINANCE: { name: 'binance', displayName: 'Binance', currency: 'usdt' },
  KRAKEN: { name: 'kraken', displayName: 'Kraken', currency: 'usd' },
  COINBASE: { name: 'coinbase', displayName: 'Coinbase', currency: 'usd' },
  BITSTAMP: { name: 'bitStamp', displayName: 'Bit Stamp', currency: 'usd' },
  CRYPTO_DOT_COM: { name: 'cryptoDotCom', displayName: 'Crypto.com', currency: 'usd' },
  BYBIT: { name: 'byBit', displayName: 'By Bit', currency: 'usdt' },
} as const;

// Type from values
export type TExchange = (typeof EXCHANGES)[keyof typeof EXCHANGES];
export type TExchangeName = (typeof EXCHANGES)[keyof typeof EXCHANGES]['name'];
