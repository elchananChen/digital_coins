import express from "express";
import {
  getOrderBook,
  getTickersCurrencies,
} from "../controllers/bitstampController";

const router = express.Router();

router.get("/tickers/Currencies", getTickersCurrencies);

router.get("/book_order/:market_symbol", getOrderBook);

export default router;
