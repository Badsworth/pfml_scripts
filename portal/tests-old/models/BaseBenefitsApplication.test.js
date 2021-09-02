import Address from "../../src/models/Address";
import BaseBenefitsApplication from "../../src/models/BaseBenefitsApplication";
import { BaseMockBenefitsApplicationBuilder } from "../test-utils";

describe("BaseBenefitsApplication", () => {
  class TestClaim extends BaseBenefitsApplication {}
  class MockTestClaimBuilder extends BaseMockBenefitsApplicationBuilder {
    constructor(middleName) {
      super();
      this.claimAttrs = {
        first_name: "Michael",
        middle_name: middleName || "",
        last_name: "Scott",
        gender: "Man",
        date_of_birth: "1980-07-17",
        tax_identifier: "1234",
      };
    }

    completed() {
      this.continuous();
      this.reducedSchedule();
      return this;
    }

    create() {
      return new TestClaim(this.claimAttrs);
    }
  }

  const expectedLeaveDetails = {
    continuous_leave_periods: null,
    employer_notification_date: null,
    intermittent_leave_periods: null,
    reason: null,
    reduced_schedule_leave_periods: null,
  };

  describe("#constructor()", () => {
    it("instantiates a model with default attributes", () => {
      const testClaim = new TestClaim();

      expect(testClaim.fineos_absence_id).toEqual(null);
      expect(testClaim.leave_details).toEqual(expectedLeaveDetails);
      expect(testClaim.residential_address).toEqual(new Address());
    });

    it("has access to getter properties", () => {
      const testClaim = new TestClaim();

      expect(testClaim.isContinuous).toBe(false);
      expect(testClaim.isIntermittent).toBe(false);
      expect(testClaim.isReducedSchedule).toBe(false);
    });
  });

  let claim,
    claimWithContinuousLeave,
    claimWithIntermittentLeave,
    claimWithMultipleLeavePeriods,
    claimWithReducedLeave;

  beforeEach(() => {
    claim = new MockTestClaimBuilder().completed().create();
    claimWithContinuousLeave = new MockTestClaimBuilder()
      .continuous({ start_date: "2021-03-01", end_date: "2021-09-01" })
      .create();
    claimWithIntermittentLeave = new MockTestClaimBuilder()
      .intermittent({ start_date: "2021-02-01", end_date: "2021-08-01" })
      .create();
    claimWithMultipleLeavePeriods = new MockTestClaimBuilder()
      .continuous({ start_date: "2021-03-01", end_date: "2021-09-01" })
      .reducedSchedule({ start_date: "2021-01-01", end_date: "2021-08-01" })
      .create();
    claimWithReducedLeave = new MockTestClaimBuilder()
      .reducedSchedule({ start_date: "2021-01-01", end_date: "2021-08-01" })
      .create();
  });

  describe("#fullName", () => {
    it("returns formatted full name", () => {
      expect(claim.fullName).toEqual("Michael Scott");
    });

    it("returns formatted name with middle name", () => {
      const claimWithMiddleName = new MockTestClaimBuilder("Gary")
        .completed()
        .create();
      expect(claimWithMiddleName.fullName).toEqual("Michael Gary Scott");
    });
  });

  it("#isBondingLeave returns true when the Claim reason is bonding", () => {
    const emptyClaim = new BaseBenefitsApplication();
    const claimWithReason = new MockTestClaimBuilder()
      .bondingLeaveReason()
      .create();

    expect(emptyClaim.isBondingLeave).toBe(false);
    expect(claimWithReason.isBondingLeave).toBe(true);
  });

  describe("#isContinuous", () => {
    it("returns true if continuous leave data is set", () => {
      expect(claimWithContinuousLeave.isContinuous).toBe(true);
      expect(claimWithIntermittentLeave.isContinuous).toBe(false);
      expect(claimWithMultipleLeavePeriods.isContinuous).toBe(true);
      expect(claimWithReducedLeave.isContinuous).toBe(false);
    });
  });

  describe("#continuousLeaveDateRange", () => {
    it("returns the expected date range", () => {
      expect(claimWithContinuousLeave.continuousLeaveDateRange()).toEqual(
        "3/1/2021 to 9/1/2021"
      );
    });
  });

  describe("#isReducedSchedule", () => {
    it("returns true if continuous leave data is set", () => {
      expect(claimWithContinuousLeave.isReducedSchedule).toBe(false);
      expect(claimWithIntermittentLeave.isReducedSchedule).toBe(false);
      expect(claimWithMultipleLeavePeriods.isReducedSchedule).toBe(true);
      expect(claimWithReducedLeave.isReducedSchedule).toBe(true);
    });
  });

  describe("#reducedLeaveDateRange", () => {
    it("returns the expected date range", () => {
      expect(claimWithReducedLeave.reducedLeaveDateRange()).toBe(
        "1/1/2021 to 8/1/2021"
      );
    });
  });

  describe("#isIntermittent", () => {
    it("returns true if continuous leave data is set", () => {
      expect(claimWithContinuousLeave.isIntermittent).toBe(false);
      expect(claimWithIntermittentLeave.isIntermittent).toBe(true);
      expect(claimWithMultipleLeavePeriods.isIntermittent).toBe(false);
      expect(claimWithReducedLeave.isIntermittent).toBe(false);
    });
  });

  describe("#intermittentLeaveDateRange", () => {
    it("returns the expected date range", () => {
      expect(claimWithIntermittentLeave.intermittentLeaveDateRange()).toEqual(
        "2/1/2021 to 8/1/2021"
      );
    });
  });

  describe("#leaveStartDate", () => {
    it("returns earliest start_date", () => {
      expect(claimWithContinuousLeave.leaveStartDate).toEqual("2021-03-01");
      expect(claimWithIntermittentLeave.leaveStartDate).toEqual("2021-02-01");
      expect(claimWithMultipleLeavePeriods.leaveStartDate).toEqual(
        "2021-01-01"
      );
      expect(claimWithReducedLeave.leaveStartDate).toEqual("2021-01-01");
    });
  });

  describe("#leaveEndDate", () => {
    it("returns latest end_date", () => {
      expect(claimWithContinuousLeave.leaveEndDate).toEqual("2021-09-01");
      expect(claimWithIntermittentLeave.leaveEndDate).toEqual("2021-08-01");
      expect(claimWithMultipleLeavePeriods.leaveEndDate).toEqual("2021-09-01");
      expect(claimWithReducedLeave.leaveEndDate).toEqual("2021-08-01");
    });
  });
});
