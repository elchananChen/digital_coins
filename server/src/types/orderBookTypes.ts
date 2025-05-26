export enum EBitstampSymbol {
  BTC_USD = "BTC-USD", // Bitcoin
  ETH_USD = "ETH-USD", // Ethereum
  LTC_USD = "LTC-USD", // Litecoin
  XRP_USD = "XRP-USD", // Ripple (XRP)
  BCH_USD = "BCH-USD", // Bitcoin Cash
}

export enum EBinanceSymbol {
  BTC_USD = "BTCUSDT", // Bitcoin
  ETH_USD = "ETHUSDT", // Ethereum
  LTC_USD = "LTCUSDT", // Litecoin
  XRP_USD = "XRPUSDT", // Ripple
  BCH_USD = "BCHUSDT", // Bitcoin Cash
}

export enum EUsdSymbol {
  BTC_USD = "BTCUSD", // Bitcoin
  ETH_USD = "ETHUSD", // Ethereum
  LTC_USD = "LTCUSD", // Litecoin
  XRP_USD = "XRPUSD", // Ripple (XRP)
  BCH_USD = "BCHUSD", // Bitcoin Cash
}

export enum EUsdtSymbol {
  BTC_USD = "BTCUSDT", // Bitcoin
  ETH_USD = "ETHUSDT", // Ethereum
  LTC_USD = "LTCUSDT", // Litecoin
  XRP_USD = "XRPUSDT", // Ripple
  BCH_USD = "BCHUSDT", // Bitcoin Cash
}

type PriceAmount = {
  price: number;
  amount: number;
};

export type TBookingSchema = {
  exchange: "coinbase" | "bitstamp" | "kraken";
  symbol: EUsdSymbol | EUsdtSymbol;
  timestamp: Date;
  bids: PriceAmount[];
  asks: PriceAmount[];
};
