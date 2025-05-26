import { Schema, model } from "mongoose";
import { EBitstampSymbol } from "../types/orderBookTypes";

const PriceAmountSchema = new Schema(
  {
    price: { type: Number, required: true },
    amount: { type: Number, required: true },
  },
  { _id: false }
);

const BookingSchema = new Schema({
  exchange: {
    type: String,
    enum: ["coinbase", "bitstamp", "kraken"],
    required: true,
  },
  symbol: {
    type: String,
    enum: Object.values(EBitstampSymbol),
    required: true,
  },
  timestamp: {
    type: Date,
    required: true,
  },

  bids: [PriceAmountSchema],
  asks: [PriceAmountSchema],
});

export const bookingModel = model("Booking", BookingSchema);
