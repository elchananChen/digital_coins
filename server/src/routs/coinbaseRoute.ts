import express from "express";
import { getCoinBaseBook } from "../controllers/coinbaseController";

const router = express.Router();

//Product Id Format BTC-USD
router.get("/products/:product_id/book", getCoinBaseBook);


export default router;



