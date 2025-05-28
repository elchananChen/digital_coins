import { Response } from "express";
import mongoose from "mongoose";

export const mongooseErrors = (error: any, res: Response, name: string) => {
  console.error(`Error fetching ${name}:`, error);

  // טיפול בשגיאות מונגוס מפורט
  if (error instanceof mongoose.Error.ValidationError) {
    return res
      .status(400)
      .json({ error: "Validation error", details: error.errors });
  }

  if (error instanceof mongoose.Error.CastError) {
    return res
      .status(400)
      .json({ error: "Invalid format for one of the fields" });
  }

  if (error instanceof mongoose.Error.DocumentNotFoundError) {
    return res.status(404).json({ error: `${name} not found` });
  }

  // MongoError - שגיאות ישירות מה־MongoDB (כמו duplicate key)
  if (error.name === "MongoError") {
    if (error.code === 11000) {
      // כפילות מפתח
      return res
        .status(409)
        .json({ error: "Duplicate key error", keyValue: error.keyValue });
    }
    // אפשר להוסיף טיפול במקרים אחרים של MongoError
    return res.status(500).json({ error: "Database error" });
  }

  // אם שגיאה אחרת - פשוט להחזיר 500 כללי
  return res.status(500).json({ error: "Internal server error" });
};
