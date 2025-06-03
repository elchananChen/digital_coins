import express from "express";
import dotenv from "dotenv";
import morgan from "morgan";
import cron from "node-cron";
import { getLocalIP } from "./utils/utils";

// routes
import liveCoinRoute from "./routs/liveCoinRoute";
import bitstampRoute from "./routs/bitstampRoute";
import coinbaseRoute from "./routs/coinbaseRoute";
import binanceRoute from "./routs/binanceRoute";
import orderbookRoute from "./routs/orderBookRoute";

import mongoose from "mongoose";
import {
  insertBinance,
  insertBitStamp,
  insertByBit,
  insertCoinbase,
  insertCryptoDotCom,
  insertKraken,
} from "./services/orderBookService";

dotenv.config();
const app = express();
const PORT = process.env.PORT || 3000;
const localIP = getLocalIP();

if (process.env.DB_URI) {
  mongoose
    .connect(process.env.DB_URI)
    .then(() => {
      console.log("Successfully Connected to DB");
      // Runs every 1 second, only if the previous run has finished
      // platforms are not depend on each other
      const platforms = [
        { name: "binance", fn: insertBinance },
        { name: "kraken", fn: insertKraken },
        { name: "coinbase", fn: insertCoinbase },
        { name: "cryptoDotCom", fn: insertCryptoDotCom },
        { name: "byBit", fn: insertByBit },
        { name: "bitStamp", fn: insertBitStamp },
      ];
      // flags
      const runningMap: Record<string, boolean> = {};

      platforms.forEach(({ name }) => {
        runningMap[name] = false;
      });

      cron.schedule("* * * * * *", () => {
        platforms.forEach(async ({ name, fn }) => {
          if (runningMap[name]) return;

          runningMap[name] = true;
          try {
            await fn();
          } catch (e) {
            console.error(`Error in ${name} job:`, e);
          } finally {
            runningMap[name] = false;
          }
        });
      });
    })
    .catch((err) => console.error("Connection to DB failed", err));
} else {
  console.error("DB_URI environment variable is not defined");
}

// middlewares
app.use(express.json());
app.use(morgan("tiny"));

//Routes
app.use("/api/live_coin", liveCoinRoute);
app.use("/api/bitstamp", bitstampRoute);
app.use("/api/coinbase", coinbaseRoute);
app.use("/api/binance", binanceRoute);
app.use("/api/order_book", orderbookRoute);

app.listen(PORT, () => {
  if (localIP) {
    console.log(`Server is running on http://${localIP}:${PORT}`);
  } else {
    console.log(`Server is running on http://localhost:${PORT}`);
  }
});
