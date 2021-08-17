import mongoose = require("mongoose");
export function MongoConnector(): {
  connectDB: (connectionURI: string) => Promise<void>;
  disconnectDB: () => Promise<void>;
} {
  let db: mongoose.Connection;
  async function connectDB(connectionURI: string): Promise<void> {
    if (db) return;
    db = mongoose.connection;
    await mongoose.connect(connectionURI, { useNewUrlParser: true });
  }
  async function disconnectDB(): Promise<void> {
    if (!db) return;
    await mongoose.disconnect();
  }
  return { connectDB, disconnectDB };
}
