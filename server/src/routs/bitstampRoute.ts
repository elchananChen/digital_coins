import express from "express";
import {
  getOrderBook,
  getTickersCurrencies,
} from "../controllers/bitstampController";

const router = express.Router();

router.get("/tickers/Currencies", getTickersCurrencies);

// market_symbol, example - btcusd
router.get("/book_order/:market_symbol", getOrderBook);

export default router;
