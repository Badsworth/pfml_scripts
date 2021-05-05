import spreadMinutesOverWeek from "../../src/utils/spreadMinutesOverWeek";

describe("spreadMinutesOverWeek", () => {
  it("splits the minutes evenly across 7 days in 15-minute increments", () => {
    const dailyMinutes = spreadMinutesOverWeek(15 * 7);
    expect(dailyMinutes).toEqual([15, 15, 15, 15, 15, 15, 15]);
  });

  it("distributes remainder of minutes when they can't be evenly split across 7 days", () => {
    const dailyMinutes = spreadMinutesOverWeek(480);
    expect(dailyMinutes).toEqual([75, 75, 75, 75, 60, 60, 60]);
  });

  it("distributes remainder of minutes in minimum 15-minute increments", () => {
    const dailyMinutes = spreadMinutesOverWeek(60 * 39 + 8);
    expect(dailyMinutes).toEqual([345, 345, 338, 330, 330, 330, 330]);
  });

  it("distributes minutes correctly when there are only full hours and less than 15 min remaining", () => {
    const dailyMinutes = spreadMinutesOverWeek(60 * 70 + 3);
    expect(dailyMinutes).toEqual([603, 600, 600, 600, 600, 600, 600]);
  });

  it("distributes minutes correctly under 15 minutes per day", () => {
    const dailyMinutes = spreadMinutesOverWeek(15 * 4 + 3);
    expect(dailyMinutes).toEqual([15, 15, 15, 15, 3, 0, 0]);
  });

  it("handles zero minutes correctly", () => {
    const dailyMinutes = spreadMinutesOverWeek(0);
    expect(dailyMinutes).toEqual([0, 0, 0, 0, 0, 0, 0]);
  });

  it("throws error if minutes null or undefined", () => {
    const nullMinutes = () => spreadMinutesOverWeek(null);
    const undefinedMinutes = () => spreadMinutesOverWeek(undefined);

    expect(nullMinutes).toThrow();
    expect(undefinedMinutes).toThrow();
  });
});
