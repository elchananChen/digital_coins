import axios, { isAxiosError } from "axios";
import { Request, Response } from "express";

export const getCoinBaseBook = async (req: Request, res: Response) => {
  try {
    // market_symbol, example - btcusd
    const { product_id } = req.params;

    const response = await axios.get(
      `https://api.exchange.coinbase.com/products/${product_id}/book?level=2`
    );

    // console.log(response.data);

    res.status(200).json(response.data);
  } catch (error) {
    if (isAxiosError(error)) {
      res
        .status(error.status || 500)
        .send({ message: error.message, code: error.code });
    }
  }
};
