import { ApplicationResponse } from "../api";
import fs from "fs";
import { GeneratedClaim } from "../generation/Claim";
import { reduce } from "streaming-iterables";
import * as ndjson from "ndjson";
import multipipe from "multipipe";
import { EOL } from "os";

export interface ClaimStateTrackerInterface {
  set(result: StateRecord): Promise<void>;
  has(id: string): Promise<boolean>;
  get(id: string): Promise<StateRecord | null>;
}

export type SubmissionResult = {
  claim: GeneratedClaim;
  result?: ApplicationResponse;
  error?: Error;
};
type StateRecord = {
  claim_id: string;
  fineos_absence_id?: string;
  error?: string;
  time?: string;
};
export type StateMap = Record<string, StateRecord>;
/**
 * This class tracks simulation progress, preventing us from re-executing the same claim.
 */
export default class ClaimStateTracker implements ClaimStateTrackerInterface {
  filename: string;
  initialized: boolean;
  records?: StateMap;

  constructor(filename: string) {
    this.filename = filename;
    this.initialized = false;
  }

  private async init(): Promise<StateMap> {
    try {
      const stream = multipipe(
        fs.createReadStream(this.filename, "utf-8"),
        ndjson.parse()
      );
      const makeStateMap = reduce((map: StateMap, record: StateRecord) => {
        map[record.claim_id] = record;
        return map;
      });
      return await makeStateMap({}, stream);
    } catch (e) {
      if (e.code === "ENOENT") {
        return {};
      }
      throw e;
    }
  }

  private async flush(record: StateRecord) {
    // Very important - this method appends one line at a time, never overwriting the file.
    // This prevents us from mistakenly nulling out the whole state file if we manage to exit
    // the process halfway through a write. Some lessons you have to learn the hard way...
    await fs.promises.appendFile(this.filename, JSON.stringify(record) + EOL, {
      encoding: "utf-8",
    });
  }

  async get(id: string): Promise<StateRecord | null> {
    if (!this.records) {
      this.records = await this.init();
    }
    if (id in this.records) {
      return this.records[id];
    }
    return null;
  }

  async set(result: StateRecord): Promise<void> {
    if (!this.records) {
      this.records = await this.init();
    }
    const record = { time: new Date().toISOString(), ...result };
    await this.flush(record);
    this.records[result.claim_id] = record;
  }

  async has(id: string): Promise<boolean> {
    if (!this.records) {
      this.records = await this.init();
    }
    return id in this.records;
  }
}
