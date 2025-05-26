import axios from "axios";
import Booking from "../models/bookOrderModel";
const BinanceSymbols = [
  "BTCUSDT", // Bitcoin
  "ETHUSDT", // Ethereum
  "LTCUSDT", // Litecoin
  "XRPUSDT", // Ripple
  "BCHUSDT", // Bitcoin Cash
];

export async function updateBinance() {
  try {
    const results = await Promise.allSettled(
      BinanceSymbols.map((symbol) =>
        axios.get(`https://api.binance.com/api/v3/depth`, {
          params: { symbol, limit: 10 },
        })
      )
    );

    results.forEach((result, index) => {
      const symbol = BinanceSymbols[index];

      if (result.status === "fulfilled") {
        const data = result.value.data;
        //         await Booking.bulkWrite([
        //   {
        //     updateOne: {
        //       filter: { exchange: "binance", symbol: "BTCUSDT" },
        //       update: { $set: { bids: , asks: [...] } },
        //       upsert: true
        //     }
        //   },

        // ]);
        console.log(`✅ ${symbol} data:`, data);
      } else {
        console.warn(`❌ Failed to fetch ${symbol}:`, result.reason);
      }
    });
  } catch (error) {
    console.error("Unexpected error:", error);
  }
}
