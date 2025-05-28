import { Schema, SchemaTypeOptions, model } from "mongoose";
import {
  EUsdSymbol,
  EUsdtSymbol,
  TOrderBookSchema,
  TPriceAmount,
} from "../types/orderBookTypes";

const PriceAmountSchema = new Schema<TPriceAmount>(
  {
    price: { type: Number, required: true },
    amount: { type: Number, required: true },
    timestamp: { type: Date },
  },
  { _id: false }
);

const symbolField: SchemaTypeOptions<EUsdSymbol | EUsdtSymbol> = {
  type: String,
  required: true,
  validate: {
    validator: function (this: any, value: string): boolean {
      const exchange = this.exchange;
      // here add all the usd exchanges
      if (exchange === "bitstamp" || exchange === "kraken") {
        return Object.values(EUsdSymbol).includes(value as EUsdSymbol);
      }
      // here add all the usdt exchanges
      if (exchange === "binance") {
        return Object.values(EUsdtSymbol).includes(value as EUsdtSymbol);
      }
      return true;
    },
    message: function (props): string {
      return `Invalid symbol '${props.value}' for the given exchange`;
    },
  },
};

const orderBookSchema = new Schema<TOrderBookSchema>({
  exchange: {
    type: String,
    enum: [
      "coinbase",
      "bitstamp",
      "binance",
      "kraken",
      "cryptoDotCom",
      "byBit",
    ],
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

// Compound index to quickly fetch the latest entry per symbol and exchange
orderBookSchema.index({ symbol: 1, exchange: 1, timestamp: -1 });

// Automatically delete data older than 10 minutes
orderBookSchema.index({ timestamp: 1 }, { expireAfterSeconds: 600 });

export default model("OrderBook", orderBookSchema, "OrderBook");
