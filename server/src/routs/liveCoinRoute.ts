import express from "express";
import { coinsList } from "../controllers/liveCoinController";

const router = express.Router();

router.post("/coins/list", coinsList);

export default router;
