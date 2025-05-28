import express from "express";
import { getBookOrder, getOrder } from "../controllers/binanceController";

const router = express.Router();

// if no query params - get all coins
// if query params symbol=BTCUSDT for example- get only  bitcoin
router.get("/book_order", getOrder);

export default router;
