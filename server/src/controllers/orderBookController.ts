import BookOrder from "../models/orderBookModel";
import { Request, Response } from "express";
import { mongooseErrors } from "../utils/errors";
import { EExchangeEnum } from "../types/exchangeTypes";

export async function getOrderBook(req: Request, res: Response) {
  try {
    const { exchange, symbol } = req.query;

    //  if no exchange in query params or in the wrong format
    if (!exchange || typeof exchange !== "string") {
      res.status(400).send({
        code: "bad request",
        message: "exchange missing in the params",
      });
      return;
    }

    //  if exchange in query params but not supported
    if (!Object.values(EExchangeEnum).includes(exchange as EExchangeEnum)) {
      res.status(400).send({
        code: "UNSUPPORTED_EXCHANGE",
        message: `Exchange "${exchange}" is not supported.`,
        supportedExchanges: Object.values(EExchangeEnum),
      });
      return;
    }

    //  if symbol send the symbol for the exchange
    if (symbol) {
      // last data for this symbol
      const data = await BookOrder.findOne({
        symbol,
        exchange,
      }).sort({ timestamp: -1 });
      res.status(200).send({ data });
      return;
    }

    // if no symbol send the last data for all symbols

    // get the symbols match the exchange
    const symbols = await BookOrder.distinct("symbol", { exchange });
    // console.log("symbols");

    // send query to get all of the symbols from this exchange
    const data = await Promise.all(
      symbols.map((symbol) =>
        BookOrder.findOne({ symbol, exchange }).sort({
          timestamp: -1,
        })
      )
    );
    // console.log(data);

    res.status(200).send({ data, message: "success" });
  } catch (error) {
    mongooseErrors(error, res, "order book");
  }
}
