import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import EmployerBenefits from "../../../src/pages/applications/employer-benefits";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (options = { hasEmployerBenefits: true }) => {
  const claim = options.hasEmployerBenefits
    ? new MockBenefitsApplicationBuilder()
        .continuous()
        .employerBenefit()
        .create()
    : new MockBenefitsApplicationBuilder().continuous().create();

  const { appLogic, wrapper } = renderWithAppLogic(EmployerBenefits, {
    claimAttrs: claim,
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

describe("EmployerBenefits", () => {
  describe("when the claim contains employer benefits data", () => {
    it("renders the page", () => {
      const { wrapper } = setup();
      expect(wrapper).toMatchSnapshot();
    });

    it("calls claims.update when user clicks continue", async () => {
      const { appLogic, claim, submitForm } = setup();

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          has_employer_benefits: claim.has_employer_benefits,
        }
      );
    });

    it("sends employer_benefits as null to the API if has_employer_benefits changes to no", async () => {
      const { appLogic, changeRadioGroup, claim, submitForm } = setup();

      changeRadioGroup("has_employer_benefits", "false");

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          has_employer_benefits: false,
          employer_benefits: null,
        }
      );
    });
  });

  describe("when the claim does not contain employer benefits data", () => {
    const disableEmployerBenefits = { hasEmployerBenefits: false };

    it("renders the page", () => {
      const { wrapper } = setup(disableEmployerBenefits);
      expect(wrapper).toMatchSnapshot();
    });

    it("sends the user's input to the API when the user clicks continue", async () => {
      const { appLogic, changeRadioGroup, claim, submitForm } = setup(
        disableEmployerBenefits
      );

      // check that "false" works
      changeRadioGroup("has_employer_benefits", false);

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          has_employer_benefits: false,
        }
      );

      // check that "true" works
      changeRadioGroup("has_employer_benefits", true);

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          has_employer_benefits: true,
        }
      );
    });
  });
});
