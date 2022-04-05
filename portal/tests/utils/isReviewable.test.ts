import MockDate from "mockdate";
import { createAbsencePeriod } from "tests/test-utils";
import { createMockManagedRequirement } from "lib/mock-helpers/createMockManagedRequirement";
import { isReviewable } from "src/utils/isReviewable";

const openAbsencePeriod = createAbsencePeriod({ request_decision: "Pending" });
const openManagedRequirement = createMockManagedRequirement({
  follow_up_date: "2022-03-03",
  status: "Open",
});
const finalAbsencePeriod = createAbsencePeriod({
  request_decision: "Cancelled",
});
const finalManagedRequirement = createMockManagedRequirement({
  follow_up_date: "2021-01-01",
});

describe("isReviewable", () => {
  beforeEach(() => {
    MockDate.set("2022-02-02");
  });

  it.each([
    createAbsencePeriod({ request_decision: "Pending" }),
    createAbsencePeriod({ request_decision: "In Review" }),
    createAbsencePeriod({ request_decision: "Projected" }),
  ])(
    "returns expected isReviewable status for variety of 'open' statuses",
    (openAbsencePeriod) => {
      expect(
        isReviewable([openAbsencePeriod], [openManagedRequirement])
      ).toBeTruthy();
      expect(
        isReviewable([finalAbsencePeriod], [finalManagedRequirement])
      ).toBeFalsy();
      expect(
        isReviewable([finalAbsencePeriod], [openManagedRequirement])
      ).toBeFalsy();
      expect(
        isReviewable([openAbsencePeriod], [finalManagedRequirement])
      ).toBeFalsy();
    }
  );

  it.each([
    createAbsencePeriod({ request_decision: "Withdrawn" }),
    createAbsencePeriod({ request_decision: "Approved" }),
    createAbsencePeriod({ request_decision: "Denied" }),
    createAbsencePeriod({ request_decision: "Cancelled" }),
    createAbsencePeriod({ request_decision: "Voided" }),
  ])(
    "returns expected isReviewable status for variety of 'final' statuses",
    (finalAbsencePeriod) => {
      expect(
        isReviewable([openAbsencePeriod], [openManagedRequirement])
      ).toBeTruthy();
      expect(
        isReviewable([finalAbsencePeriod], [finalManagedRequirement])
      ).toBeFalsy();
      expect(
        isReviewable([finalAbsencePeriod], [openManagedRequirement])
      ).toBeFalsy();
      expect(
        isReviewable([openAbsencePeriod], [finalManagedRequirement])
      ).toBeFalsy();
    }
  );
});
