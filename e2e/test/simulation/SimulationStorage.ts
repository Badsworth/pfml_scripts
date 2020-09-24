import { describe, it, expect } from "@jest/globals";
import SimulationStorage from "../../src/simulation/SimulationStorage";

describe("SimulationStorage", () => {
  const storage = new SimulationStorage("/tmp/sim");
  it("Should return a correct documents directory", () => {
    expect(storage.documentDirectory).toBe("/tmp/sim/documents");
  });

  it("Should return a correct claims file", () => {
    expect(storage.claimFile).toBe("/tmp/sim/claims.json");
  });

  it("Should return a correct state tracker", () => {
    expect(storage.stateFile).toBe("/tmp/sim/state.json");
  });

  it("Should return a correct mail directory", () => {
    expect(storage.mailDirectory).toEqual("/tmp/sim/mail");
  });
});
