import generate from "../../src/simulation/generate";
// Explicitly import jest globals to avoid clash with Cypress globals.
import { describe, expect, it } from "@jest/globals";

/**
 * This file tests that our generation code works.
 *
 * We have tests for this because business simulation is run
 * infrequently, and breakage could leave a simulation half-run.
 */
describe("Business Simulation Generator", () => {
  it("Should produce a valid birth date", () => {
    const app = generate();
    expect(app.date_of_birth).toMatch(/\d{4}-\d{2}-\d{2}/);
  });
});
