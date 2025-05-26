import express from "express";
import dotenv from "dotenv";
import morgan from "morgan";
import { getLocalIP } from "./utils/utils";

// routes
import liveCoinRoute from "./routs/liveCoinRoute";
import bitstampRoute from "./routs/bitstampRoute";
import coinbaseRoute from "./routs/coinbaseRoute";

import mongoose from "mongoose";
dotenv.config();
const app = express();
const PORT = process.env.PORT || 3000;
const localIP = getLocalIP();

if (process.env.DB_URI) {
  mongoose
    .connect(process.env.DB_URI)
    .then(() => console.log("Successfully Connected to DB"))
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

app.listen(PORT, () => {
  if (localIP) {
    console.log(`Server is running on http://${localIP}:${PORT}`);
  } else {
    console.log(`Server is running on http://localhost:${PORT}`);
  }
});
