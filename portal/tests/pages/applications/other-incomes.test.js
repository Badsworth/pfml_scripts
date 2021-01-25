import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import OtherIncomes from "../../../src/pages/applications/other-incomes";

jest.mock("../../../src/hooks/useAppLogic");

describe("OtherIncomes", () => {
  let appLogic, changeRadioGroup, claim, submitForm, wrapper;

  beforeEach(() => {
    claim = new MockClaimBuilder().continuous().otherIncome().create();

    ({ appLogic, wrapper } = renderWithAppLogic(OtherIncomes, {
      claimAttrs: claim,
    }));

    ({ changeRadioGroup, submitForm } = simulateEvents(wrapper));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  // MockClaimBuilder sets defaults for other_incomes_awaiting_approval to
  // false and has_other_incomes to true. The following 3 tests ensure
  // that making a selection calls handleHasOtherIncomesChange() and updates
  // both fields to the expected values.
  describe("when user selects a radio and clicks continue", () => {
    it("calls claims.update with expected API fields when user selects Yes", async () => {
      changeRadioGroup("has_other_incomes", "yes");

      await submitForm();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          other_incomes_awaiting_approval: false,
          has_other_incomes: true,
        }
      );
    });

    it("calls claims.update with expected API fields when user selects No", async () => {
      changeRadioGroup("has_other_incomes", "no");

      await submitForm();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          other_incomes_awaiting_approval: false,
          other_incomes: null,
          has_other_incomes: false,
        }
      );
    });

    it("calls claims.update with expected API fields when user selects Not Yet", async () => {
      changeRadioGroup("has_other_incomes", "pending");

      await submitForm();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          other_incomes_awaiting_approval: true,
          has_other_incomes: false,
        }
      );
    });
  });
});
