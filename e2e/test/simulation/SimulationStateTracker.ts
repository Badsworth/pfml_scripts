import { describe, it, expect } from "@jest/globals";
import fs from "fs";
import path from "path";
import os from "os";
import { SimulationStateFileTracker } from "../../src/simulation/SimulationStateTracker";

describe("SimulationStateTracker", () => {
  let filename: string;

  beforeEach(async () => {
    const dir = await fs.promises.mkdtemp(path.join(os.tmpdir(), "state"));
    filename = path.join(dir, "state.json");
  });

  it("Should track state", async () => {
    const tracker = new SimulationStateFileTracker(filename);
    expect(await tracker.has("foo")).toBe(false);
    await tracker.set("foo", { foo: "bar" }, false);
    expect(await tracker.has("foo")).toBe(true);
  });

  it("Should be capable of reading state from a previous tracker", async () => {
    await new SimulationStateFileTracker(filename).set("foo", { foo: "bar" });
    expect(await new SimulationStateFileTracker(filename).has("foo")).toBe(
      true
    );
  });

  it("Should be capable of resetting errors", async () => {
    const t1 = new SimulationStateFileTracker(filename);
    await t1.set("a", {}, true);
    await t1.set("b", {}, false);
    await t1.resetErrors();
    expect(await t1.has("a")).toBe(false);
    expect(await t1.has("b")).toBe(true);
    const t2 = new SimulationStateFileTracker(filename);
    expect(await t2.has("a")).toBe(false);
    expect(await t2.has("b")).toBe(true);
  });
});
