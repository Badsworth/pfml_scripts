import { describe, it, expect } from "@jest/globals";
import { SubmissionResult } from "../../../src/submission/ClaimStateTracker";
import { consume } from "streaming-iterables";
import {
  logSubmissions,
  watchFailures,
} from "../../../src/submission/iterable";

const successResult = {
  claim: { id: "123", scenario: "BHAP1" },
  result: { fineos_absence_id: "NTN-123" },
} as SubmissionResult;

const errorResult = {
  claim: { id: "456", scenario: "BHAP1" },
  error: new Error("Testing"),
} as SubmissionResult;

describe("logSubmissions", () => {
  const output: string[] = [];
  let error: jest.SpyInstance;
  let log: jest.SpyInstance;
  let debug: jest.SpyInstance;
  beforeEach(() => {
    error = jest
      .spyOn(console, "error")
      .mockImplementation((o) => output.push(o));
    log = jest.spyOn(console, "log").mockImplementation((o) => output.push(o));
    debug = jest
      .spyOn(console, "debug")
      .mockImplementation((o) => output.push(o));
  });
  afterEach(() => {
    error.mockRestore();
    log.mockRestore();
    debug.mockRestore();
  });

  it("Should produce a log entry for each submission", async () => {
    await consume(logSubmissions([successResult, errorResult]));
    expect(output.join("\n")).toContain("Submission completed for NTN-123");
    expect(output.join("\n")).toContain("Submission ended in an error.");
  });
});

describe("watchFailures", () => {
  it("Should not error when there is a success in between 3 failures", async () => {
    const results = [errorResult, errorResult, successResult, errorResult];
    await expect(consume(watchFailures(results))).resolves.toBe(undefined);
  });

  it("Should error when 3 consecutive failures are encountered", async () => {
    const results = [errorResult, errorResult, errorResult];
    await expect(consume(watchFailures(results))).rejects.toThrowError();
  });
});
