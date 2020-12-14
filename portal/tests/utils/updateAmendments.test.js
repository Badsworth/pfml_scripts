import EmployerBenefit, {
  EmployerBenefitType,
} from "../../src/models/EmployerBenefit";
import updateAmendments from "../../src/utils/updateAmendments";

describe("updateAmendments", () => {
  const partialBenefit = {
    employer_benefit_id: 1,
    benefit_start_date: "new-start-date",
  };
  const existingBenefit = new EmployerBenefit({
    benefit_amount_dollars: 1000,
    benefit_end_date: "end-date",
    benefit_start_date: "start-date",
    benefit_type: EmployerBenefitType.shortTermDisability,
    employer_benefit_id: 1,
  });

  it("returns an array with updated values", () => {
    const expectedBenefits = updateAmendments(
      [existingBenefit],
      partialBenefit
    );

    const {
      employer_benefit_id,
      benefit_type,
      benefit_amount_dollars,
      benefit_end_date,
      benefit_start_date,
    } = expectedBenefits[0];
    expect(employer_benefit_id).toEqual(1);
    expect(benefit_type).toEqual(EmployerBenefitType.shortTermDisability);
    expect(benefit_amount_dollars).toEqual(1000);
    expect(benefit_end_date).toEqual("end-date");
    expect(benefit_start_date).toEqual("new-start-date");
  });

  it("returns an array with existing values if no amended values are provided", () => {
    const expectedBenefits = updateAmendments([existingBenefit], {});

    expect(expectedBenefits).toEqual([existingBenefit]);
  });

  it("returns an array with existing values if id of amended value does not match", () => {
    const partialBenefit = {
      employer_benefit_id: 2,
      benefit_start_date: "new-start-date",
    };

    const expectedBenefits = updateAmendments(
      [existingBenefit],
      partialBenefit
    );

    expect(expectedBenefits).toEqual([existingBenefit]);
  });
});
