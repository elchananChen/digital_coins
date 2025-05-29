import { ExchangeType } from "./exchangeTypes";

// ! symbols format for our DB (EUsdSymbol ,EUsdtSymbol)
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

// ! exchanges symbols format
export enum ECoinbaseBitstampSymbol {
  BTC_USD = "BTC-USD", // Bitcoin
  ETH_USD = "ETH-USD", // Ethereum
  LTC_USD = "LTC-USD", // Litecoin
  XRP_USD = "XRP-USD", // Ripple (XRP)
  BCH_USD = "BCH-USD", // Bitcoin Cash
}
export enum ECryptoDotComSymbol {
  BTC_USD = "BTC_USD", // Bitcoin
  ETH_USD = "ETH_USD", // Ethereum
  LTC_USD = "LTC_USD", // Litecoin
  XRP_USD = "XRP_USD", // Ripple (XRP)
  BCH_USD = "BCH_USD", // Bitcoin Cash
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

// ! schema
export type TPriceAmount = {
  price: number;
  amount: number;
  timestamp?: Date;
};

export type TOrderBookSchema = {
  exchange: ExchangeType;
  symbol: EUsdSymbol | EUsdtSymbol;
  timestamp: Date;
  bids: TPriceAmount[];
  asks: TPriceAmount[];
};

// ! platforms

export type TKrakenCoinbaseOrder = [string, string, number];
export type TCryptoDotComOrder = [string, string, string];
export type TBinanceByBitOrder = [string, string];

export type TBinanceOrderBookResults = {
  // lastUpdateId: number;
  bids: TBinanceByBitOrder[];
  asks: TBinanceByBitOrder[];
};

export type TKrakenOrderBookResults = {
  error: string[];
  result: {
    [pair: string]: {
      asks: TKrakenCoinbaseOrder[];
      bids: TKrakenCoinbaseOrder[];
    };
  };
};

export type TCoinbaseOrderBookResults = {
  time?: string;
  bids: TKrakenCoinbaseOrder[];
  asks: TKrakenCoinbaseOrder[];
};

export type TCryptoDotComOrderBookResults = {
  result: {
    data: [
      {
        bids: TCryptoDotComOrder[];
        asks: TCryptoDotComOrder[];
        t?: number;
      }
    ];
  };
};

export type TByBitOrderBookResults = {
  result: {
    a: TBinanceByBitOrder[];
    b: TBinanceByBitOrder[];
    cts?: number;
  };
};
