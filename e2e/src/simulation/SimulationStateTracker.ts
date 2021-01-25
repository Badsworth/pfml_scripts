import fs from "fs";

type ExecutionMap = Record<string, ExecutionRecord>;
type ExecutionRecord = { result?: string; error?: string; time: string };

export default interface SimulationStateTracker {
  set(id: string, result?: string, error?: string): Promise<void>;
  has(id: string): Promise<boolean>;
  get(id: string): Promise<ExecutionRecord | null>;
}

/**
 * This class tracks simulation progress, preventing us from re-executing the same claim.
 */
export class SimulationStateFileTracker implements SimulationStateTracker {
  filename: string;
  initialized: boolean;
  records?: ExecutionMap;

  constructor(filename: string) {
    this.filename = filename;
    this.initialized = false;
  }

  private async init(): Promise<ExecutionMap> {
    try {
      const contents = await fs.promises.readFile(this.filename, "utf-8");
      return JSON.parse(contents);
    } catch (e) {
      if (e.code === "ENOENT") {
        return {};
      }
      throw e;
    }
  }

  private async flush(records: ExecutionMap) {
    await fs.promises.writeFile(this.filename, JSON.stringify(records));
  }

  async get(id: string): Promise<ExecutionRecord | null> {
    if (!this.records) {
      this.records = await this.init();
    }
    if (id in this.records) {
      return this.records[id];
    }
    return null;
  }

  async set(id: string, result?: string, error?: string): Promise<void> {
    if (!this.records) {
      this.records = await this.init();
    }
    this.records[id] = { result, error, time: new Date().toISOString() };
    await this.flush(this.records);
  }

  async has(id: string): Promise<boolean> {
    if (!this.records) {
      this.records = await this.init();
    }
    return id in this.records;
  }

  async resetErrors(): Promise<void> {
    const records = await this.init().then(
      (records): ExecutionMap => {
        const entries = Object.entries(records).filter(
          (entry) => entry[1].error === undefined
        );
        return Object.fromEntries(entries);
      }
    );
    await this.flush(records);
    this.records = records;
  }
}

export class SimulationStateNullTracker implements SimulationStateTracker {
  set(): Promise<void> {
    return Promise.resolve();
  }
  has(): Promise<boolean> {
    return Promise.resolve(false);
  }
  get(): Promise<null> {
    return Promise.resolve(null);
  }
}
