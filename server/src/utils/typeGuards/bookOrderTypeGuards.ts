import {
  TBinanceByBitOrder,
  TBinanceOrderBookResults,
  TBitStampResults,
  TByBitOrderBookResults,
  TCoinbaseOrderBookResults,
  TCryptoDotComOrder,
  TCryptoDotComOrderBookResults,
  TKrakenCoinbaseOrder,
  TKrakenOrderBookResults,
} from "../../types/orderBookTypes";

// binance
export const binanceOrderBookTypeGuard = (
  data: any
): data is TBinanceOrderBookResults => {
  return (
    typeof data === "object" &&
    data !== null &&
    "bids" in data &&
    Array.isArray(data.bids) &&
    data.bids.every(
      (entry: any): entry is [string, string] =>
        entry.length > 1 &&
        typeof entry[0] === "string" &&
        typeof entry[1] === "string"
    ) &&
    "asks" in data &&
    data.asks.every(
      (entry: any): entry is [string, string] =>
        entry.length > 1 &&
        typeof entry[0] === "string" &&
        typeof entry[1] === "string"
    )
  );
};

// kraken
export const krakenOrderBookTypeGuard = (
  data: any
): data is TKrakenOrderBookResults => {
  return (
    typeof data === "object" &&
    data !== null &&
    "result" in data &&
    typeof data.result === "object" &&
    data.result !== null &&
    Object.values(data.result).every((entry: any) => {
      return (
        typeof entry === "object" &&
        Array.isArray(entry.bids) &&
        Array.isArray(entry.asks) &&
        krakenCoinbaseOrderCheck(entry.asks) &&
        krakenCoinbaseOrderCheck(entry.bids)
      );
    })
  );
};

// coinbase
export const coinbaseOrderBookTypeGuard = (
  data: any
): data is TCoinbaseOrderBookResults => {
  return (
    typeof data === "object" &&
    data !== null &&
    Array.isArray(data.bids) &&
    Array.isArray(data.asks) &&
    krakenCoinbaseOrderCheck(data.bids.slice(0, 10)) &&
    krakenCoinbaseOrderCheck(data.asks.slice(0, 10))
    // typeof data.time === "string" &&
    // !isNaN(Date.parse(data.time))
  );
};

// coinbase
export const bitStampTypeGuard = (data: any): data is TBitStampResults => {
  return (
    typeof data === "object" &&
    data !== null &&
    Array.isArray(data.bids) &&
    Array.isArray(data.asks) &&
    binanceByBitOrderCheck(data.bids.slice(0, 10)) &&
    binanceByBitOrderCheck(data.asks.slice(0, 10))
  );
};

// cryptoDotCom
export const cryptoDotComTypeGuard = (
  data: any
): data is TCryptoDotComOrderBookResults => {
  if (
    typeof data !== "object" ||
    data === null ||
    typeof data.result !== "object" ||
    data.result === null ||
    !Array.isArray(data.result.data) ||
    data.result.data.length === 0
  ) {
    return false;
  }

  const book = data.result.data[0];
  return (
    typeof book === "object" &&
    book !== null &&
    "bids" in book &&
    "asks" in book &&
    CryptoDotComOrderCheck(book.bids) &&
    CryptoDotComOrderCheck(book.asks)
  );
};

// byBit
export const byBitOrderBookTypeGuard = (
  data: any
): data is TByBitOrderBookResults => {
  if (
    typeof data !== "object" ||
    data === null ||
    typeof data.result !== "object" ||
    data.result === null
  ) {
    return false;
  }

  const { a, b } = data.result;

  return (
    Array.isArray(a) &&
    Array.isArray(b) &&
    binanceByBitOrderCheck(a) &&
    binanceByBitOrderCheck(b)
  );
};

// for bids and asks with [string, string , number]
export const krakenCoinbaseOrderCheck = (
  orders: any
): orders is TKrakenCoinbaseOrder[] => {
  return (
    Array.isArray(orders) &&
    orders.every(
      (entry: any) =>
        Array.isArray(entry) &&
        entry.length === 3 &&
        typeof entry[0] === "string" &&
        typeof entry[1] === "string" &&
        typeof entry[2] === "number"
    )
  );
};

// for bids and asks with [string, string , string]
export const CryptoDotComOrderCheck = (
  orders: any
): orders is TCryptoDotComOrder[] => {
  return (
    Array.isArray(orders) &&
    orders.every(
      (entry: any) =>
        Array.isArray(entry) &&
        entry.length === 3 &&
        typeof entry[0] === "string" &&
        typeof entry[1] === "string" &&
        typeof entry[2] === "string"
    )
  );
};

// for bids and asks with [string, string]
export const binanceByBitOrderCheck = (
  orders: any
): orders is TBinanceByBitOrder[] => {
  return (
    Array.isArray(orders) &&
    orders.every(
      (entry: any) =>
        Array.isArray(entry) &&
        entry.length === 2 &&
        typeof entry[0] === "string" &&
        typeof entry[1] === "string"
    )
  );
};
