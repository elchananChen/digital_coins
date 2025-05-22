import express from "express";
import dotenv from "dotenv";
import morgan from "morgan";
import { getLocalIP } from "./utils/utils";

// routes
import liveCoinRoute from "./routs/liveCoinRoute";
import bitstampRoute from "./routs/bitstampRoute";
dotenv.config();
const app = express();
const PORT = process.env.PORT || 3000;
const localIP = getLocalIP();

// middlewares
app.use(express.json());
app.use(morgan("tiny"));

app.use("/api/live_coin", liveCoinRoute);
app.use("/api/bitstamp", bitstampRoute);
app.listen(PORT, () => {
  if (localIP) {
    console.log(`Server is running on http://${localIP}:${PORT}`);
  } else {
    console.log(`Server is running on http://localhost:${PORT}`);
  }
});
