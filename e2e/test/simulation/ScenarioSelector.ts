import ScenarioSelector from "../../src/simulation/ScenarioSelector";
import { PortalApplicationSubmission } from "../../src/simulation/types";
// Explicitly import jest globals to avoid clash with Cypress globals.
import { describe, expect, it } from "@jest/globals";

describe("ScenarioSelector", () => {
  it("Should generate according to probability", () => {
    const first = {} as PortalApplicationSubmission;
    const second = {} as PortalApplicationSubmission;

    const selector = new ScenarioSelector();
    selector.add(1, () => first);
    selector.add(3, () => second);

    const counts = [0, 0];
    for (let i = 0; i < 100; i++) {
      const x = selector.spin();
      if (x === first) {
        counts[0]++;
      } else if (x === second) {
        counts[1]++;
      } else {
        throw new Error("Invalid submission returned.");
      }
    }
    expect(counts[0]).toBeLessThan(counts[1]);
  });
});
