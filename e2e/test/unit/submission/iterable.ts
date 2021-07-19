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

  it("Should not error when 3 consecutive failures are encountered if otherwise specified", async () => {
    const results = [errorResult, errorResult, errorResult, errorResult];
    await expect(consume(watchFailures(results, 5, true))).resolves.toBe(
      undefined
    );
  });

  it("Should error when 'n' consecutive failures are encountered", async () => {
    const results = [errorResult, errorResult, errorResult, errorResult];
    await expect(
      consume(watchFailures(results, 4, true))
    ).rejects.toThrowError();
  });

  it("Should reset consecutive errors to 3 if there is one successful submission after 6 errors", async () => {
    const results = [
      errorResult, // 1
      errorResult, // 2
      errorResult, // 3
      errorResult, // 4
      errorResult, //5
      errorResult, // 6
      successResult, // 3
      errorResult, // 4
      errorResult, // 5
      errorResult, // 6
      errorResult, // 7
      errorResult, // 8
      errorResult, // 9
    ];

    await expect(
      consume(watchFailures(results, 9, true))
    ).rejects.toThrowError();

    await expect(consume(watchFailures(results, 10, true))).resolves.toBe(
      undefined
    );
  });

  // proves that if consecutive errors are greater than 6 (highly unstable claim submission), we won't continue with full speed claim submission until we see more stability
  it("Should reset consecutive errors to 0 if 1 of the 3 subseqeuent submissions are succesful after 6 errors", async () => {
    const results = [
      errorResult, // 1
      errorResult, // 2
      errorResult, // 3
      errorResult, // 4
      errorResult, // 5
      errorResult, // 6
      successResult, // 3
      errorResult, // 4
      errorResult, // 5
      successResult, // 0
      errorResult, // 1
      errorResult, // 2
      errorResult, // 3
      errorResult, // 4
      errorResult, // 5
      errorResult, // 6
      errorResult, // 7
    ];
    await expect(
      consume(watchFailures(results, 7, true))
    ).rejects.toThrowError();
    await expect(consume(watchFailures(results, 10, true))).resolves.toBe(
      undefined
    );
  });
});
