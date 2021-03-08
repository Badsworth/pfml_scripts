import { ApplicationResponse } from "../api";
import fs from "fs";
import { GeneratedClaim } from "../generation/Claim";
import { filter, tap } from "streaming-iterables";

export interface ClaimStateTrackerInterface {
  set(id: string, result: StateRecord): Promise<void>;
  has(id: string): Promise<boolean>;
  get(id: string): Promise<StateRecord | null>;
}

export type SubmissionResult = {
  claim: GeneratedClaim;
  result?: ApplicationResponse;
  error?: Error;
};
type StateRecord = {
  fineos_absence_id?: string;
  error?: string;
  time?: string;
};
type StateMap = Record<string, StateRecord>;
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
      const contents = await fs.promises.readFile(this.filename, "utf-8");
      return JSON.parse(contents);
    } catch (e) {
      if (e.code === "ENOENT") {
        return {};
      }
      throw e;
    }
  }

  private async flush(records: StateMap) {
    await fs.promises.writeFile(this.filename, JSON.stringify(records));
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

  /**
   * An iterator callback to filter out claims that have already been submitted.
   */
  filter = filter(
    async (claim: GeneratedClaim): Promise<boolean> => {
      return this.has(claim.id).then((r) => !r);
    }
  );

  /**
   * An iterator callback to mark claims as submitted as they are processed.
   */
  track = tap(
    async (result: SubmissionResult): Promise<void> => {
      await this.set(result.claim.id, {
        fineos_absence_id: result.result?.fineos_absence_id,
        error: result.error?.message,
      });
    }
  );

  async set(id: string, result: StateRecord): Promise<void> {
    if (!this.records) {
      this.records = await this.init();
    }
    this.records[id] = { time: new Date().toISOString(), ...result };
    await this.flush(this.records);
  }

  async has(id: string): Promise<boolean> {
    if (!this.records) {
      this.records = await this.init();
    }
    return id in this.records;
  }
}
