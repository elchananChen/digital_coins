import axios from "axios";
import OrderBook from "../models/orderBookModel";
import {
  BinanceOrderBookTypeGuard,
  KrakenOrderBookTypeGuard,
} from "../utils/typeGuards/bookOrderTypeGuards";
import {
  EKrakenSymbol,
  EUsdtSymbol,
  TOrderBookSchema,
} from "../types/orderBookTypes";
import { KrakenSymbolsToUsdSymbols } from "../utils/utils";

//  extract the EUsdtSymbols to an array
const BinanceSymbols: EUsdtSymbol[] = Object.values(EUsdtSymbol);
const KrakenSymbols: EKrakenSymbol[] = Object.values(EKrakenSymbol);

//! binance
export async function insertBinance() {
  try {
    const results = await Promise.allSettled(
      BinanceSymbols.map((symbol) =>
        axios.get(`https://api.binance.com/api/v3/depth`, {
          params: { symbol, limit: 10 },
        })
      )
    );

    const timestamp = new Date();
    const validBookings: TOrderBookSchema[] = [];

    results.forEach((result, index) => {
      const symbol = BinanceSymbols[index];

      if (
        result.status === "fulfilled" &&
        BinanceOrderBookTypeGuard(result.value.data)
      ) {
        const data = result.value.data;

        validBookings.push({
          exchange: "binance",
          symbol,
          timestamp,
          bids: data.bids.map(([p, a]) => ({
            price: parseFloat(p),
            amount: parseFloat(a),
          })),
          asks: data.asks.map(([p, a]) => ({
            price: parseFloat(p),
            amount: parseFloat(a),
          })),
        });
        // console.log(`✅ ${symbol} data:`, data);
      } else if (result.status === "fulfilled") {
        console.log(`partial ${symbol} data:`, result.value.data);
      } else {
        console.warn(
          `❌ Failed to fetch binance order book ${symbol}:`,
          result.reason
        );
      }
    });

    if (validBookings.length > 0) {
      const bulkOps = validBookings.map((booking) => ({
        updateOne: {
          filter: { symbol: booking.symbol, exchange: "binance" },
          update: { $set: booking },
          upsert: true,
        },
      }));

      await OrderBook.bulkWrite(bulkOps);
      console.log(
        `🗂️ Update ${validBookings.length} Binance order books into DB.`
      );
    }
  } catch (error) {
    console.error("Unexpected error:", error);
  }
}

// ! kraken
export async function insertKraken() {
  try {
    const results = await Promise.allSettled(
      KrakenSymbols.map((symbol) =>
        axios.get(`https://api.kraken.com/0/public/Depth`, {
          params: { pair: symbol, count: 10 },
        })
      )
    );

    const timestamp = new Date();
    const validOrderBook: TOrderBookSchema[] = [];

    results.forEach((result, index) => {
      const krakenSymbol = KrakenSymbols[index];
      const symbol = KrakenSymbolsToUsdSymbols(krakenSymbol);

      // * if type TKrakenOrderBookResults
      if (
        result.status === "fulfilled" &&
        KrakenOrderBookTypeGuard(result.value.data)
      ) {
        const data = result.value.data;

        // Kraken returns a dynamic symbol key (e.g., "XXBTZUSD"), which we don't care about.
        // So we destructure the object and take only the value (the order data).
        const [_, orderData] = Object.entries(data.result)[0];

        validOrderBook.push({
          exchange: "kraken",
          symbol,
          timestamp,
          bids: orderData.bids.map(([p, a]) => ({
            price: parseFloat(p),
            amount: parseFloat(a),
          })),
          asks: orderData.asks.map(([p, a]) => ({
            price: parseFloat(p),
            amount: parseFloat(a),
          })),
        });
        // * if data not match TKrakenOrderBookResults
      } else if (result.status === "fulfilled") {
        console.log(`partial ${symbol} data:`, result.value.data);
        // * if error
      } else {
        console.warn(
          `❌ Failed to fetch kraken order book ${symbol}:`,
          result.reason
        );
      }
    });

    //  if there are any good data update db
    if (validOrderBook.length > 0) {
      // const bulkOps = validOrderBook.map((orderBook) => ({
      //   updateOne: {
      //     filter: { symbol: orderBook.symbol, exchange: "kraken" },
      //     update: { $set: orderBook },
      //     upsert: true,
      //   },
      // }));

      await OrderBook.insertMany(validOrderBook, { ordered: false });
      console.log(
        `🗂️ Update ${validOrderBook.length} Kraken order books into DB.`
      );
    }
  } catch (error) {
    console.error("Unexpected error:", error);
  }
}
