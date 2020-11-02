import { describe, it, expect } from "@jest/globals";
import SimulationStorage from "../../src/simulation/SimulationStorage";
import os from "os";
import path from "path";

describe("SimulationStorage", () => {
  const tempdir = os.tmpdir();
  const dir = path.join(tempdir, "sim");
  const storage = new SimulationStorage(dir);
  it("Should return a correct documents directory", () => {
    expect(storage.documentDirectory).toBe(path.join(dir, "documents"));
  });

  it("Should return a correct claims file", () => {
    expect(storage.claimFile).toBe(path.join(dir, "claims.json"));
  });

  it("Should return a correct state tracker", () => {
    expect(storage.stateFile).toBe(path.join(dir, "state.json"));
  });

  it("Should return a correct mail directory", () => {
    expect(storage.mailDirectory).toBe(path.join(dir, "mail"));
  });
});
