import axios from "axios";
import OrderBook from "../models/orderBookModel";
import {
  binanceOrderBookTypeGuard,
  byBitOrderBookTypeGuard,
  coinbaseOrderBookTypeGuard,
  cryptoDotComTypeGuard,
  krakenOrderBookTypeGuard,
} from "../utils/typeGuards/bookOrderTypeGuards";
import {
  ECoinbaseBitstampSymbol,
  ECryptoDotComSymbol,
  EKrakenSymbol,
  EUsdtSymbol,
  TOrderBookSchema,
} from "../types/orderBookTypes";
import {
  CoinbaseSymbolsToUsdSymbols,
  CryptoDotComSymbolsToUsdSymbols,
  KrakenSymbolsToUsdSymbols,
} from "../utils/utils";
import { log } from "console";

//  extract the EUsdtSymbols to an array
const binanceSymbols: EUsdtSymbol[] = Object.values(EUsdtSymbol);
const krakenCoinbaseSymbols: EKrakenSymbol[] = Object.values(EKrakenSymbol);
const coinbaseSymbols: ECoinbaseBitstampSymbol[] = Object.values(
  ECoinbaseBitstampSymbol
);
const cryptoDotComSymbols: ECryptoDotComSymbol[] =
  Object.values(ECryptoDotComSymbol);

//! binance
export async function insertBinance() {
  try {
    const results = await Promise.allSettled(
      binanceSymbols.map((symbol) =>
        axios.get(`https://api.binance.com/api/v3/depth`, {
          params: { symbol, limit: 10 },
        })
      )
    );
 
    const timestamp = new Date();
    const validOrderBook: TOrderBookSchema[] = [];

    results.forEach((result, index) => {
      const symbol = binanceSymbols[index];

      if (
        result.status === "fulfilled" &&
        binanceOrderBookTypeGuard(result.value.data)
      ) {
        const data = result.value.data;

        validOrderBook.push({
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
          result.reason.code,
          result.reason.status
        );
      }
    });

    if (validOrderBook.length > 0) {
      await OrderBook.insertMany(validOrderBook, { ordered: false });
      console.log(
        `🗂️ Insert ${validOrderBook.length} binance order books into DB.`
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
      krakenCoinbaseSymbols.map((symbol) =>
        axios.get(`https://api.kraken.com/0/public/Depth`, {
          params: { pair: symbol, count: 10 },
        })
      )
    );

    const timestamp = new Date();
    const validOrderBook: TOrderBookSchema[] = [];

    results.forEach((result, index) => {
      const krakenSymbol = krakenCoinbaseSymbols[index];
      const symbol = KrakenSymbolsToUsdSymbols(krakenSymbol);

      // * if type TKrakenOrderBookResults
      if (
        result.status === "fulfilled" &&
        krakenOrderBookTypeGuard(result.value.data)
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
          result.reason.code,
          result.reason.status
        );
      }
    });

    // * if there are any good data update db
    if (validOrderBook.length > 0) {
      await OrderBook.insertMany(validOrderBook, { ordered: false });
      console.log(
        `🗂️ Insert ${validOrderBook.length} Kraken order books into DB.`
      );
    }
  } catch (error) {
    console.error("Unexpected error:", error);
  }
}

// ! coinbase
export async function insertCoinbase() {
  try {
    const results = await Promise.allSettled(
      coinbaseSymbols.map((product_id) =>
        axios.get(
          `https://api.exchange.coinbase.com/products/${product_id}/book`,
          {
            params: { level: 2 },
          }
        )
      )
    );

    const validOrderBook: TOrderBookSchema[] = [];
    let timestamp = new Date();

    results.forEach((result, index) => {
      const coinbaseSymbol = coinbaseSymbols[index];

      // work for coinbase too
      const symbol = CoinbaseSymbolsToUsdSymbols(coinbaseSymbol);

      // * if type TCoinbaseOrderBookResults
      if (
        result.status === "fulfilled" &&
        coinbaseOrderBookTypeGuard(result.value.data)
      ) {
        const data = result.value.data;

        // If 'time' exists, set 'timestamp' to its value
        if (data.time && !isNaN(Date.parse(data.time))) {
          timestamp = new Date(data.time);
        }

        validOrderBook.push({
          exchange: "coinbase",
          symbol,
          timestamp: timestamp,
          bids: data.bids.slice(0, 10).map(([p, a]) => ({
            price: parseFloat(p),
            amount: parseFloat(a),
          })),
          asks: data.asks.slice(0, 10).map(([p, a]) => ({
            price: parseFloat(p),
            amount: parseFloat(a),
          })),
        });
        // * if data not match TCoinbaseOrderBookResults
      } else if (result.status === "fulfilled") {
        console.log(`partial ${symbol} data:`, result.value.data);
        // * if error
      } else {
        console.warn(
          `❌ Failed to fetch coinbase order book ${symbol}:`,
          result.reason.code,
          result.reason.status
        );
      }
    });

    // * if there are any good data - insert to the db
    if (validOrderBook.length > 0) {
      await OrderBook.insertMany(validOrderBook, { ordered: false });
      console.log(
        `🗂️ Insert ${validOrderBook.length} coinbase order books into DB.`
      );
    }
  } catch (error) {
    console.error("Unexpected error:", error);
  }
}

// !crypto.com
export async function insertCryptoDotCom() {
  try {
    const results = await Promise.allSettled(
      cryptoDotComSymbols.map((instrument_name) =>
        axios.get(`https://api.crypto.com/exchange/v1/public/get-book`, {
          params: { instrument_name, depth: 10 },
        })
      )
    );

    const validOrderBook: TOrderBookSchema[] = [];
    let timestamp = new Date();

    results.forEach((result, index) => {
      const cryptoDotComSymbol = cryptoDotComSymbols[index];

      const symbol = CryptoDotComSymbolsToUsdSymbols(cryptoDotComSymbol);

      // * if type TCoinbaseOrderBookResults
      if (
        result.status === "fulfilled" &&
        cryptoDotComTypeGuard(result.value.data)
      ) {
        const data = result.value.data.result.data[0];

        // If 't' exists, set 'timestamp' to its value
        const now = Date.now();
        if (
          typeof data.t === "number" &&
          data.t > 0 &&
          data.t < now + 1000 * 60 // not a future date
        ) {
          timestamp = new Date(data.t);
        }

        // if the data valid - push to an array that will add to DB
        validOrderBook.push({
          exchange: "cryptoDotCom",
          symbol,
          timestamp: timestamp,
          bids: data.bids.slice(0, 10).map(([p, a]) => ({
            price: parseFloat(p),
            amount: parseFloat(a),
          })),
          asks: data.asks.slice(0, 10).map(([p, a]) => ({
            price: parseFloat(p),
            amount: parseFloat(a),
          })),
        });

        // * if data not match  TCryptoDotComOrderBookResults
      } else if (result.status === "fulfilled") {
        console.log(`partial ${symbol} data:`, result.value.data);
        // * if error
      } else {
        console.warn(
          `❌ Failed to fetch crypto.com order book ${symbol}:`,
          result.reason.code,
          result.reason.status
        );
      }
    });

    // * if there are any good data - insert to the DB
    if (validOrderBook.length > 0) {
      await OrderBook.insertMany(validOrderBook, { ordered: false });
      console.log(
        `🗂️ Insert ${validOrderBook.length} crypto.com order books into DB.`
      );
    }
  } catch (error) {
    console.error("Unexpected error:", error);
  }
}

// ! byBit
export async function insertByBit() {
  try {
    const results = await Promise.allSettled(
      binanceSymbols.map((symbol) =>
        axios.get(`https://api.bybit.com/v5/market/orderbook`, {
          params: { symbol, category: "spot", limit: 10 },
        })
      )
    );

    const validOrderBook: TOrderBookSchema[] = [];
    let timestamp = new Date();

    results.forEach((result, index) => {
      // same symbols
      const symbol = binanceSymbols[index];

      // * if type TByBitOrderBookResults
      if (
        result.status === "fulfilled" &&
        byBitOrderBookTypeGuard(result.value.data)
      ) {
        const data = result.value.data.result;

        // If 'cts' exists, set 'timestamp' to its value
        const now = Date.now();
        if (
          typeof data.cts === "number" &&
          data.cts > 0 &&
          data.cts < now + 1000 * 60 // not a future date
        ) {
          timestamp = new Date(data.cts);
        }

        // if the data valid - push to an array that will add to DB
        validOrderBook.push({
          exchange: "byBit",
          symbol,
          timestamp: timestamp,
          bids: data.b.map(([p, a]) => ({
            price: parseFloat(p),
            amount: parseFloat(a),
          })),
          asks: data.a.map(([p, a]) => ({
            price: parseFloat(p),
            amount: parseFloat(a),
          })),
        });

        // * if data not match  TByBitOrderBookResults
      } else if (result.status === "fulfilled") {
        console.log(`partial ${symbol} data:`, result.value.data);
        // * if error
      } else {
        console.warn(
          `❌ Failed to fetch byBit order book ${symbol}:`,
          result.reason.code,
          result.reason.status
        );
      }
    });

    // * if there are any good data - insert to the DB
    if (validOrderBook.length > 0) {
      await OrderBook.insertMany(validOrderBook, { ordered: false });
      console.log(
        `🗂️ Insert ${validOrderBook.length} byBit order books into DB.`
      );
    }
  } catch (error) {
    console.error("Unexpected error:", error);
  }
}
