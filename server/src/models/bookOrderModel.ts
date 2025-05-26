import mongoose, { Schema, SchemaTypeOptions, model } from "mongoose";
import {
  EBinanceSymbol,
  EBitstampSymbol,
  EUsdSymbol,
  EUsdtSymbol,
  TBookingSchema,
} from "../types/orderBookTypes";

const PriceAmountSchema = new Schema(
  {
    price: { type: Number, required: true },
    amount: { type: Number, required: true },
  },
  { _id: false }
);

const symbolField: SchemaTypeOptions<EUsdSymbol | EUsdtSymbol> = {
  type: String,
  required: true,
  validate: {
    validator: function (this: any, value: string): boolean {
      const exchange = this.exchange;
      if (exchange === "bitstamp") {
        return Object.values(EUsdSymbol).includes(value as EUsdSymbol);
      }
      if (exchange === "binance") {
        return Object.values(EUsdtSymbol).includes(value as EUsdtSymbol);
      }
      return true;
    },
    message: function (props): string {
      // כאן אין גישה ל־this.exchange אז נציין הודעה כללית
      return `Invalid symbol '${props.value}' for the given exchange`;
    },
  },
};

const BookingSchema = new Schema<TBookingSchema>({
  exchange: {
    type: String,
    enum: ["coinbase", "bitstamp", "binance", "kraken"], // הוספתי binance
    required: true,
  },
  symbol: symbolField,
  timestamp: {
    type: Date,
    required: true,
  },
  bids: [PriceAmountSchema],
  asks: [PriceAmountSchema],
});

export default model("Booking", BookingSchema);
