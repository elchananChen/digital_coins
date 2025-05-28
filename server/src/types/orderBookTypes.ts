export enum EBitstampSymbol {
  BTC_USD = "BTC-USD", // Bitcoin
  ETH_USD = "ETH-USD", // Ethereum
  LTC_USD = "LTC-USD", // Litecoin
  XRP_USD = "XRP-USD", // Ripple (XRP)
  BCH_USD = "BCH-USD", // Bitcoin Cash
}
export enum EKrakenSymbol {
  BTC_USD = "btcusd", // Bitcoin
  ETH_USD = "ethusd", // Ethereum
  LTC_USD = "ltcusd", // Litecoin
  XRP_USD = "xrpusd", // Ripple (XRP)
  BCH_USD = "bchusd", // Bitcoin Cash
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

export type TPriceAmount = {
  price: number;
  amount: number;
  timestamp?: Date;
};

export type TOrderBookSchema = {
  exchange: "coinbase" | "bitstamp" | "kraken" | "binance";
  symbol: EUsdSymbol | EUsdtSymbol;
  timestamp: Date;
  bids: TPriceAmount[];
  asks: TPriceAmount[];
};

export type TBinanceOrderBookResults = {
  // lastUpdateId: number;
  bids: [string, string][];
  asks: [string, string][];
};

type KrakenOrder = [string, string, number];

export type TKrakenOrderBookResults = {
  error: string[];
  result: {
    [pair: string]: {
      asks: KrakenOrder[];
      bids: KrakenOrder[];
    };
  };
};
