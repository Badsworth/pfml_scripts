import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import OtherIncomes from "../../../src/pages/applications/other-incomes";

jest.mock("../../../src/hooks/useAppLogic");

const otherIncomeClaim = new MockBenefitsApplicationBuilder()
  .continuous()
  .otherIncome()
  .create();

const setup = (
  claimAttrs = new MockBenefitsApplicationBuilder().continuous().create()
) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(OtherIncomes, {
    claimAttrs,
  });

  const { changeRadioGroup, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeRadioGroup,
    claim,
    submitForm,
    wrapper,
  };
};

describe("OtherIncomes", () => {
  it("renders the page", () => {
    const { wrapper } = setup();
    expect(wrapper).toMatchSnapshot();
  });

  it("calls claims.update with expected API fields when user selects Yes", async () => {
    const { appLogic, claim, changeRadioGroup, submitForm } = setup(
      otherIncomeClaim
    );

    changeRadioGroup("has_other_incomes", "true");

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_other_incomes: true,
      }
    );
  });

  it("calls claims.update with expected API fields when user selects No", async () => {
    const { appLogic, claim, changeRadioGroup, submitForm } = setup();

    changeRadioGroup("has_other_incomes", "false");

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_other_incomes: false,
      }
    );
  });

  it("calls claims.update with expected API fields when claim already has data", () => {
    const { appLogic, claim, submitForm } = setup(otherIncomeClaim);

    submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_other_incomes: true,
      }
    );
  });

  it("sets other_leaves to null when the user selects No", () => {
    const { appLogic, claim, changeRadioGroup, submitForm } = setup(
      otherIncomeClaim
    );

    expect(claim.other_incomes).toHaveLength(1);

    changeRadioGroup("has_other_incomes", "false");

    submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        other_incomes: null,
        has_other_incomes: false,
      }
    );
  });
});
