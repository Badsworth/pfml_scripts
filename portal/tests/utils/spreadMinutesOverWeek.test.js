import spreadMinutesOverWeek from "../../src/utils/spreadMinutesOverWeek";

describe("spreadMinutesOverWeek", () => {
  it("splits the minutes evenly across 7 days", () => {
    const dailyMinutes = spreadMinutesOverWeek(630);
    expect(dailyMinutes).toEqual([90, 90, 90, 90, 90, 90, 90]);
  });

  it("distributes remainder of minutes when they can't be evenly split across 7 days", () => {
    const dailyMinutes = spreadMinutesOverWeek(480);
    expect(dailyMinutes).toEqual([69, 69, 69, 69, 68, 68, 68]);
  });

  it("throws error if minutes null or undefined", () => {
    const nullMinutes = () => spreadMinutesOverWeek(null);
    const undefinedMinutes = () => spreadMinutesOverWeek(undefined);

    expect(nullMinutes).toThrow();
    expect(undefinedMinutes).toThrow();
  });
});
