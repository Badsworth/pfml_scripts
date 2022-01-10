import convertMinutesToHours from "../../src/utils/convertMinutesToHours";

describe("convertMinutesToHours", () => {
  it("converts minutes into an object with hours and minutes", () => {
    expect(convertMinutesToHours(67)).toEqual({ hours: 1, minutes: 7 });
    expect(convertMinutesToHours(600)).toEqual({ hours: 10, minutes: 0 });
  });

  it("converts null value into an object with 0 hours and minutes", () => {
    expect(convertMinutesToHours(null)).toEqual({ hours: 0, minutes: 0 });
  });
});
