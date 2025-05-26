import axios, { isAxiosError } from "axios";
import { Request, Response } from "express";

// get currencies

export const getTickersCurrencies = async (req: Request, res: Response) => {
  try {
    const response = await axios.get(
      "https://www.bitstamp.net/api/v2/currencies"
    );

    // console.log(response.data);

    res.status(200).json(response.data);
  } catch (error) {
    console.log(error);
    res.status(500).send({ message: "internal server error" });
  }
};

// get order book
export const getOrderBook = async (req: Request, res: Response) => {
  try {
    // market_symbol, example - btcusd
    const { market_symbol } = req.params;

    const response = await axios.get(
      `https://www.bitstamp.net/api/v2/order_book/${market_symbol}`
    );

    res.status(200).json(response.data);
  } catch (error) {
    if (isAxiosError(error)) {
      res
        .status(error.status || 500)
        .send({ message: error.message, code: error.code });
    }
  }
};
