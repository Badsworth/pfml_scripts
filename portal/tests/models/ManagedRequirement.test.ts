import {
  getLatestFollowUpDate,
  getSoonestReviewableFollowUpDate,
  getSoonestReviewableManagedRequirement,
} from "../../src/models/ManagedRequirement";
import MockDate from "mockdate";
import { createMockManagedRequirement } from "../../lib/mock-helpers/createMockManagedRequirement";

const MOCK_CURRENT_ISO_DATE = "2021-05-01";

describe("getLatestFollowUpDate", () => {
  it("return the most recent follow up date", () => {
    expect(
      getLatestFollowUpDate([
        createMockManagedRequirement({ follow_up_date: "2021-02-22" }),
        createMockManagedRequirement({ follow_up_date: "2021-01-22" }),
        createMockManagedRequirement({ follow_up_date: "2021-03-22" }),
      ])
    ).toBe("2021-03-22");
  });

  it("return null when there are no managed requirements", () => {
    expect(getLatestFollowUpDate([])).toBeNull();
  });
});

describe("getClosestReviewableManagedRequirement", () => {
  beforeAll(() => {
    MockDate.set(MOCK_CURRENT_ISO_DATE);
  });

  it("returns null if there is no managed requirement", () => {
    expect(getSoonestReviewableManagedRequirement([])).toBeNull();
  });

  it("returns null if there is no open managed requirement", () => {
    expect(
      getSoonestReviewableManagedRequirement([
        createMockManagedRequirement({ status: "Complete" }),
      ])
    ).toBeNull();
  });

  it("returns null if there is an open managed requirement but its follow up date is in the past", () => {
    expect(
      getSoonestReviewableManagedRequirement([
        createMockManagedRequirement({
          follow_up_date: "2021-01-01",
          status: "Open",
        }),
      ])
    ).toBeNull();
  });

  it("returns the managed requirement with the closest follow update", () => {
    expect(
      getSoonestReviewableManagedRequirement([
        createMockManagedRequirement({
          follow_up_date: "2021-06-01",
          status: "Suppressed",
        }),
        createMockManagedRequirement({ follow_up_date: "2021-08-22" }),
        createMockManagedRequirement({ follow_up_date: MOCK_CURRENT_ISO_DATE }),
        createMockManagedRequirement({ follow_up_date: "2021-09-22" }),
      ])
    ).toEqual(
      expect.objectContaining({ follow_up_date: MOCK_CURRENT_ISO_DATE })
    );
  });
});

describe("getClosestReviewableFollowUpDate", () => {
  beforeAll(() => {
    MockDate.set(MOCK_CURRENT_ISO_DATE);
  });

  it("return the formatted follow up date", () => {
    expect(
      getSoonestReviewableFollowUpDate([
        createMockManagedRequirement({ follow_up_date: "2021-08-22" }),
      ])
    ).toBe("8/22/2021");
  });

  it("returns null if there is no managed requirement", () => {
    expect(getSoonestReviewableFollowUpDate([])).toBeNull();
  });

  it("returns null if there is no open managed requirement", () => {
    expect(
      getSoonestReviewableFollowUpDate([
        createMockManagedRequirement({ status: "Complete" }),
      ])
    ).toBeNull();
  });

  it("returns null if there is an open managed requirement but its follow up date is in the past", () => {
    expect(
      getSoonestReviewableFollowUpDate([
        createMockManagedRequirement({
          follow_up_date: "2021-01-01",
          status: "Open",
        }),
      ])
    ).toBeNull();
  });

  it("returns the closest follow update if there are multiple open managed requirement", () => {
    expect(
      getSoonestReviewableFollowUpDate([
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
