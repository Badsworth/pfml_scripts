import * as Mongoose from "mongoose";
import dotenv from "dotenv";
dotenv.config();
let database: Mongoose.Connection;
export const connect = () => {
  // add your own uri below
  if (database) {
    return;
  }
  Mongoose.connect(process.env.MONGO_CONNECTION_URI as string);
  database = Mongoose.connection;
  database.once("open", async () => {
    console.log("Connected to database");
  });
  database.on("error", () => {
    console.log("Error connecting to database");
  });
};
export const disconnect = (): void => {
  if (!database) {
    return;
  }
  Mongoose.disconnect();
};
