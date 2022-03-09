import EmployerBenefit, {
  EmployerBenefitType,
} from "../../src/models/EmployerBenefit";
import PreviousLeave, {
  PreviousLeaveReason,
} from "../../src/models/PreviousLeave";
import updateAmendments from "../../src/utils/updateAmendments";

describe("updateAmendments", () => {
  const END_DATE = "end-date";
  const START_DATE = "start-date";
  const NEW_START_DATE = "new-start-date";
  const employerBenefit = new EmployerBenefit({
    benefit_end_date: END_DATE,
    benefit_start_date: START_DATE,
    benefit_type: EmployerBenefitType.shortTermDisability,
    employer_benefit_id: "1",
  });
  const previousLeave = new PreviousLeave({
    leave_end_date: END_DATE,
    leave_reason: PreviousLeaveReason.medical,
    leave_start_date: START_DATE,
    previous_leave_id: "2",
  });
  const benefitAmendment = {
    employer_benefit_id: "1",
    benefit_amount_dollars: 5000,
  };
  const leaveAmendment = {
    previous_leave_id: "2",
    leave_start_date: NEW_START_DATE,
  };

  describe("when the amendment is a valid type", () => {
    it("returns modified array for employer benefits", () => {
      const updatedBenefits = updateAmendments(
        [employerBenefit],
        benefitAmendment
      );
      const benefit = updatedBenefits[0];

      expect(benefit instanceof EmployerBenefit).toEqual(true);
      expect(benefit).toEqual({
        ...employerBenefit,
        benefit_amount_dollars: 5000,
      });
    });

    it("returns modified array for previous leaves", () => {
      const updatedLeaves = updateAmendments([previousLeave], leaveAmendment);
      const leave = updatedLeaves[0];

      expect(leave instanceof PreviousLeave).toEqual(true);
      expect(leave).toEqual({
        ...previousLeave,
        leave_start_date: NEW_START_DATE,
      });
    });
  });

  it("returns unmodified array with existing amendments if no amendedments are provided", () => {
    const updatedBenefits = updateAmendments([employerBenefit], {});

    expect(updatedBenefits).toEqual([employerBenefit]);
  });

  it("returns unmodified array with existing amendments if amendment is not instance of PreviousLeave or EmployerBenefit", () => {
    const leaveWithoutPreviousLeaveType = {
      leave_end_date: END_DATE,
      leave_reason: PreviousLeaveReason.activeDutyFamily,
      leave_start_date: START_DATE,
    };
    const updatedLeaves = updateAmendments(
      // @ts-expect-error We're intentionally testing the behavior of updateAmendments with an invalid type
      [leaveWithoutPreviousLeaveType],
      leaveAmendment
    );

    expect(updatedLeaves).toEqual([leaveWithoutPreviousLeaveType]);
  });

  it("returns unmodified array with existing amendments if id does not match", () => {
    const benefitAmendment = {
      employer_benefit_id: 2,
      benefit_start_date: NEW_START_DATE,
    };

    const updatedBenefits = updateAmendments(
      [employerBenefit],
      benefitAmendment
    );

    expect(updatedBenefits).toEqual([employerBenefit]);
  });
});
