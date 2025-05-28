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

import mongoose from "mongoose";
import { insertBinance, insertKraken } from "./services/orderBookService";

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
      let isRunning = false;
      cron.schedule("* * * * * *", async () => {
        if (isRunning) return;
        isRunning = true;
        try {
          await insertBinance();
          await insertKraken();
        } catch (e) {
          console.error("Error in cron job", e);
        } finally {
          isRunning = false;
        }
      });
      // updateKraken();
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

app.listen(PORT, () => {
  if (localIP) {
    console.log(`Server is running on http://${localIP}:${PORT}`);
  } else {
    console.log(`Server is running on http://localhost:${PORT}`);
  }
});
