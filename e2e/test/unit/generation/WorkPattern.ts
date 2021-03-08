import { describe, expect, it } from "@jest/globals";
import generateWorkPattern from "../../../src/generation/WorkPattern";

describe("Work pattern generator", () => {
  it("Should generate a fixed work pattern", () => {
    const pattern = generateWorkPattern("0,480");
    expect(pattern.work_week_starts).toEqual("Monday");
    expect(pattern.work_pattern_type).toEqual("Fixed");
    expect(pattern.work_pattern_days?.length).toBe(7);
    expect(pattern.work_pattern_days).toMatchSnapshot();
  });

  it("Should generate a rotating work pattern", () => {
    const pattern = generateWorkPattern("0,480;480,0");
    expect(pattern.work_week_starts).toEqual("Monday");
    expect(pattern.work_pattern_type).toEqual("Rotating");
    expect(pattern.work_pattern_days?.length).toBe(14);
    expect(pattern.work_pattern_days).toMatchSnapshot();
  });
});
