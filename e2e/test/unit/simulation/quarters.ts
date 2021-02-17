import quarters, { parseISODateAsLocal } from "../../../src/simulation/quarters";
import { describe, it, expect } from "@jest/globals";

describe("Quarters", () => {
  it("Should calculate the last 4 quarters from a reference date", () => {
    expect(quarters(new Date("2020-08-04 23:59:59.999"))).toEqual([
      new Date("2019-09-30 23:59:59.999"),
      new Date("2019-12-31 23:59:59.999"),
      new Date("2020-03-31 23:59:59.999"),
      new Date("2020-06-30 23:59:59.999"),
    ]);
  });
});

describe("parse", () => {
  it("Should parse an ISO date string into the local time", () => {
    expect(parseISODateAsLocal("2020-01-01")).toEqual(
      new Date("2020-01-01 00:00:00.000")
    );
  });
});
