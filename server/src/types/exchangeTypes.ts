export enum EExchangeEnum {
  COINBASE = "coinbase",
  BITSTAMP = "bitStamp",
  BINANCE = "binance",
  KRAKEN = "kraken",
  CRYPTO_DOT_COM = "cryptoDotCom",
  BYBIT = "byBit",
}

export type ExchangeType = (typeof EExchangeEnum)[keyof typeof EExchangeEnum];
