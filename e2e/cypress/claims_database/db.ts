import mongoose = require("mongoose");
let db: mongoose.Connection;

export const connectDB = async (connectionURI: string): Promise<void> => {
  if (db) return;
  db = mongoose.connection;
  await mongoose.connect(connectionURI, { useNewUrlParser: true });
};

export const disconnectDB = async (): Promise<void> => {
  if (!db) return;
  await mongoose.disconnect();
};
