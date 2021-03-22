import fs from "fs";
import path from "path";
import os from "os";
import { expect, it } from "@jest/globals";
import ClaimStateTracker from "../../../src/submission/ClaimStateTracker";

describe("ClaimStateTracker", () => {
  let filename: string;

  beforeEach(async () => {
    const dir = await fs.promises.mkdtemp(path.join(os.tmpdir(), "state"));
    filename = path.join(dir, "state.json");
  });

  it("Should track state", async () => {
    const tracker = new ClaimStateTracker(filename);
    await expect(tracker.has("foo")).resolves.toBe(false);
    await tracker.set({
      claim_id: "foo",
    });
    await expect(tracker.has("foo")).resolves.toBe(true);
    await expect(tracker.has("bar")).resolves.toBe(false);
  });

  it("Should track state after a reload", async () => {
    const _tracker = new ClaimStateTracker(filename);
    await _tracker.set({ claim_id: "foo" });
    await _tracker.set({ claim_id: "bar" });

    const tracker = new ClaimStateTracker(filename);
    await expect(tracker.has("foo")).resolves.toBe(true);
    await expect(tracker.has("bar")).resolves.toBe(true);
    await expect(tracker.has("baz")).resolves.toBe(false);
    await expect(tracker.get("foo")).resolves.toEqual({
      claim_id: "foo",
      time: expect.any(String),
    });
  });
});
