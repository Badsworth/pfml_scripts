import { AbsencePeriod } from "src/models/AbsencePeriod";
import EmployerClaim from "../../src/models/EmployerClaim";
import LeaveReason from "src/models/LeaveReason";

describe("EmployerClaim", () => {
  describe("#constructor", () => {
    it("instantiates AbsencePeriod for absence_period entries", () => {
      const claim = new EmployerClaim({
        absence_periods: [
          {
            absence_period_start_date: "2021-03-16",
            absence_period_end_date: "2021-03-30",
            fineos_leave_request_id: "abc123",
            request_decision: "Pending",
            reason: LeaveReason.bonding,
            reason_qualifier_one: "",
            reason_qualifier_two: "",
            period_type: "Reduced Schedule",
          },
        ],
      });

      expect(claim.absence_periods).toHaveLength(1);
      expect(claim.absence_periods[0]).toBeInstanceOf(AbsencePeriod);
    });
  });
});
