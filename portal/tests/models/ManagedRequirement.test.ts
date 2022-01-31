import MockDate from "mockdate";
import { createMockManagedRequirement } from "../../lib/mock-helpers/createMockManagedRequirement";
import { getClosestReviewableFollowUpDate } from "../../src/models/ManagedRequirement";

const MOCK_CURRENT_ISO_DATE = "2021-05-01";

describe("getClosestReviewableFollowUpDate", () => {
  beforeAll(() => {
    MockDate.set(MOCK_CURRENT_ISO_DATE);
  });

  it("return the formatted follow up date", () => {
    expect(
      getClosestReviewableFollowUpDate([
        createMockManagedRequirement({ follow_up_date: "2021-08-22" }),
      ])
    ).toBe("8/22/2021");
  });

  it("returns undefined if there is no managed requirement", () => {
    expect(getClosestReviewableFollowUpDate([])).toBe(undefined);
  });

  it("returns undefined if there is no open managed requirement", () => {
    expect(
      getClosestReviewableFollowUpDate([
        createMockManagedRequirement({ status: "Complete" }),
      ])
    ).toBe(undefined);
  });

  it("returns undefined if there is an open managed requirement but its follow up date is in the past", () => {
    expect(
      getClosestReviewableFollowUpDate([
        createMockManagedRequirement({
          follow_up_date: "2021-01-01",
          status: "Open",
        }),
      ])
    ).toBe(undefined);
  });

  it("returns the closest follow update if there are multiple open managed requirement", () => {
    expect(
      getClosestReviewableFollowUpDate([
        createMockManagedRequirement({
          follow_up_date: "2021-06-01",
          status: "Suppressed",
        }),
        createMockManagedRequirement({ follow_up_date: "2021-08-22" }),
        createMockManagedRequirement({ follow_up_date: MOCK_CURRENT_ISO_DATE }),
        createMockManagedRequirement({ follow_up_date: "2021-09-22" }),
      ])
    ).toBe("5/1/2021");
  });
});
