import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import EmployerBenefits from "../../../src/pages/applications/employer-benefits";

jest.mock("../../../src/hooks/useAppLogic");

describe("EmployerBenefits", () => {
  let appLogic, claim, submitForm, wrapper;

  beforeEach(() => {
    claim = new MockClaimBuilder().continuous().create();
    ({ appLogic, wrapper } = renderWithAppLogic(EmployerBenefits, {
      claimAttrs: claim,
    }));

    ({ submitForm } = simulateEvents(wrapper));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when user clicks continue", () => {
    it("calls claims.update", async () => {
      await submitForm();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          has_employer_benefits: claim.has_employer_benefits,
        }
      );
    });

    it("sends employer_benefits as null to the API if has_employer_benefits changes to no", async () => {
      claim = new MockClaimBuilder().continuous().employerBenefit().create();

      ({ appLogic, wrapper } = renderWithAppLogic(EmployerBenefits, {
        claimAttrs: claim,
      }));

      const { changeRadioGroup, submitForm } = simulateEvents(wrapper);

      changeRadioGroup("has_employer_benefits", "false");

      await submitForm();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          has_employer_benefits: false,
          employer_benefits: null,
        }
      );
    });
  });
});
