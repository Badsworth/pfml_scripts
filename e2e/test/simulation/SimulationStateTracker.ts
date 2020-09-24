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
});
