import express from "express";
import dotenv from "dotenv";
import morgan from "morgan";
import liveCoin from "./routs/liveCoinRoute";
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// middlewares
app.use(express.json());
app.use(morgan("tiny"));

app.use("/api/liveCoin", liveCoin);

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
