import { BinanceOrderBookTypeGuard } from "../../src/utils/typeGuards/bookOrderTypeGuards";
import { TBinanceOrderBookResults } from "../../src/types/orderBookTypes"; // עדכן לפי המיקום האמיתי

describe("bookOrderTypeGuard", () => {
  it("should return true for valid Binance order book structure", () => {
    const data: any = {
      bids: [["109320.00000000", "3.87023000"]],
      asks: [["109321.00000000", "1.00000000"]],
    };

    expect(BinanceOrderBookTypeGuard(data)).toBe(true);
  });

  it("should return false if bids is missing", () => {
    const data: any = {
      asks: [["109321.00000000", "1.00000000"]],
    };

    expect(BinanceOrderBookTypeGuard(data)).toBe(false);
  });

  it("should return false if bids is not an array", () => {
    const data: any = {
      bids: "not-an-array",
      asks: [["109321.00000000", "1.00000000"]],
    };

    expect(BinanceOrderBookTypeGuard(data)).toBe(false);
  });

  it("should return false if an entry in bids is not a tuple", () => {
    const data: any = {
      bids: [["109320.00000000"]], // רק ערך אחד במקום שניים
      asks: [["109321.00000000", "1.00000000"]],
    };

    expect(BinanceOrderBookTypeGuard(data)).toBe(false);
  });

  it("should return false if bid values are not strings", () => {
    const data: any = {
      bids: [[109320.0, 3.87]], // מספרים ולא מחרוזות
      asks: [["109321.00000000", "1.00000000"]],
    };

    expect(BinanceOrderBookTypeGuard(data)).toBe(false);
  });

  it("should return false if top-level object is null", () => {
    expect(BinanceOrderBookTypeGuard(null)).toBe(false);
  });

  it("should return false if object has extra unexpected structure", () => {
    const data: any = {
      bids: [["109320.00000000", "3.87023000"]],
      asks: [["109321.00000000", "1.00000000"]],
      extra: true, // תקף, אבל לא מזיק — הגארד עדיין יאשר
    };

    expect(BinanceOrderBookTypeGuard(data)).toBe(true);
  });
});
