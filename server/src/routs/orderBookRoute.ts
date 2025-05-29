import express from "express";
import { getOrderBook } from "../controllers/orderBookController";

const router = express.Router();

router.get("/", getOrderBook);

export default router;
