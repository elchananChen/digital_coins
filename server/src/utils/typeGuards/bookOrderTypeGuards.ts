import {
  TBinanceOrderBookResults,
  TKrakenOrderBookResults,
} from "../../types/orderBookTypes";

// binance
export const BinanceOrderBookTypeGuard = (
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
export const KrakenOrderBookTypeGuard = (
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
        entry.bids.every(
          (bid: any) =>
            Array.isArray(bid) &&
            bid.length === 3 &&
            typeof bid[0] === "string" && // price
            typeof bid[1] === "string" && // amount
            typeof bid[2] === "number" // timestamp
        ) &&
        entry.asks.every(
          (ask: any) =>
            Array.isArray(ask) &&
            ask.length === 3 &&
            typeof ask[0] === "string" && // price
            typeof ask[1] === "string" && // amount
            typeof ask[2] === "number" // timestamp
        )
      );
    })
  );
};
