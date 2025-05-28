import BookOrder from "../models/orderBookModel";
import { Request, Response } from "express";
import { mongooseErrors } from "../utils/errors";

export async function getBookOrder(req: Request, res: Response) {
  try {
    const { symbol } = req.query;
    if (!symbol) {
      const data = await BookOrder.findOne({ exchange: "binance" });
      res.status(200).send({ data });
      return;
    }
    const data = await BookOrder.findOne({ symbol, exchange: "binance" });
    console.log(data);
    res.status(200).send({ data });
  } catch (error) {
    mongooseErrors(error, res, "order book");
  }
}

export async function getOrder(req: Request, res: Response) {
  try {
    const { symbol } = req.query;

    if (symbol) {
      // last data for this symbol
      const data = await BookOrder.findOne({
        symbol,
        exchange: "binance",
      }).sort({ timestamp: -1 });
      res.status(200).send({ data });
      return;
    }

    // last data for all symbols
    const symbols = await BookOrder.distinct("symbol", { exchange: "binance" });
    console.log("symbols");

    const data = await Promise.all(
      symbols.map((symbol) =>
        BookOrder.findOne({ symbol, exchange: "binance" }).sort({
          timestamp: -1,
        })
      )
    );
    console.log(data);

    res.status(200).send({ data });
  } catch (error) {
    mongooseErrors(error, res, "order book");
  }
}
