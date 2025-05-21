import axios from "axios";
import { Request, Response } from "express";

const baseUrl = "https://api.livecoinwatch.com";

export const coinsList = async (req: Request, res: Response) => {
  if (!process.env.LiveCoinKey) throw new Error("api key missing!");
  try {
    axios.post(`${baseUrl}/`);
  } catch (error) {}
};
