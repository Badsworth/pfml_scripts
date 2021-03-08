import { describe, expect, it } from "@jest/globals";
import { WorkPattern } from "../../../src/api";
import { generateLeaveDates } from "../../../src/generation/LeaveDetails";
import { format } from "date-fns";

describe("Leave date generator", () => {
  it("Should always generate a correct date for a given work schedule.", () => {
    const schedule: WorkPattern = {
      work_pattern_days: [{ day_of_week: "Monday", minutes: 10 }],
    };
    for (let i = 0; i < 1000; i++) {
      const [start] = generateLeaveDates(schedule);
      expect(format(start, "iiii")).toEqual("Monday");
    }
  });
});
