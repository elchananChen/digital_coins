import axios, { isAxiosError } from "axios";
import dotenv from "dotenv";
import { Request, Response } from "express";
dotenv.config();
const baseUrl = "https://api.livecoinwatch.com";
const apiKey = process.env.LiveCoinKey || "";

export const coinsList = async (
  req: Request<{}, {}, TCoinsListBody>,
  res: Response
) => {
  if (!process.env.LiveCoinKey) throw new Error("api key missing!");
  // console.log("body:", req.body);
  // console.log("apiKey:", apiKey);

  try {
    const response = await axios.post(
      `${baseUrl}/coins/list`,
      req.body, // your request body (if any)
      {
        headers: {
          "x-api-key": apiKey,
        },
      }
    );

    // console.log(response.data);
    res.status(response.status).send(response.data);
  } catch (error) {
    // console.error("Request failed:", error);
    if (isAxiosError(error)) {
      res
        .status(error.status || 500)
        .send({ message: error.message, code: error.code });
    }
  }
};
