import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import { EmploymentStatus } from "../../../src/models/BenefitsApplication";
import EmploymentStatusPage from "../../../src/pages/applications/employment-status";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(
    EmploymentStatusPage,
    {
      claimAttrs: claimAttrs || new MockBenefitsApplicationBuilder().create(),
    }
  );
  const { changeField, changeRadioGroup, submitForm } = simulateEvents(wrapper);
  return {
    appLogic,
    changeField,
    changeRadioGroup,
    claim,
    submitForm,
    wrapper,
  };
};

const notificationFeinQuestionWrapper = (wrapper) => {
  return wrapper.find({ name: "employer_fein" });
};

describe("EmploymentStatusPage", () => {
  describe("when claimantShowEmploymentStatus feature flag is disabled", () => {
    beforeEach(() => {
      process.env.featureFlags = {
        claimantShowEmploymentStatus: false,
      };
    });

    it("renders the page without the employment status field", () => {
      const { wrapper } = setup();
      expect(wrapper).toMatchSnapshot();
      expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    });

    it("submits status and FEIN", () => {
      const { appLogic, claim, changeField, submitForm } = setup();
      const testFein = 123456789;
      changeField("employer_fein", testFein);

      submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          employment_status: EmploymentStatus.employed,
          employer_fein: testFein,
        }
      );
    });
  });

  describe("when claimantShowEmploymentStatus feature flag is enabled", () => {
    beforeEach(() => {
      process.env.featureFlags = {
        claimantShowEmploymentStatus: true,
      };
    });

    it("renders the page with the employment status field", () => {
      const { wrapper } = setup();
      expect(wrapper).toMatchSnapshot();
    });

    describe("when user selects employed in MA as their employment status", () => {
      it("shows FEIN question", () => {
        const { changeRadioGroup, wrapper } = setup();
        changeRadioGroup("employment_status", EmploymentStatus.employed);

        expect(
          notificationFeinQuestionWrapper(wrapper)
            .parents("ConditionalContent")
            .prop("visible")
        ).toBeTruthy();
      });

      it("submits status and FEIN", () => {
        const { appLogic, claim, changeField, changeRadioGroup, submitForm } =
          setup();
        changeRadioGroup("employment_status", EmploymentStatus.employed);
        const testFein = 123456789;
        changeField("employer_fein", testFein);
        submitForm();

        expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            employment_status: EmploymentStatus.employed,
            employer_fein: testFein,
          }
        );
      });
    });

    describe("when user selects self-employed as their employment status", () => {
      it("hides FEIN question", () => {
        const { changeRadioGroup, wrapper } = setup();
        changeRadioGroup("employment_status", EmploymentStatus.selfEmployed);
        expect(
          notificationFeinQuestionWrapper(wrapper)
            .parents("ConditionalContent")
            .prop("visible")
        ).toBeFalsy();
      });

      it("submits status and empty FEIN", () => {
        const { appLogic, claim, changeRadioGroup, submitForm } = setup();
        changeRadioGroup("employment_status", EmploymentStatus.selfEmployed);
        submitForm();

        expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            employment_status: EmploymentStatus.selfEmployed,
            employer_fein: null,
          }
        );
      });
    });

    describe("when user selects unemployed as their employment status", () => {
      it("hides FEIN question", () => {
        const { changeRadioGroup, wrapper } = setup();
        changeRadioGroup("employment_status", EmploymentStatus.unemployed);
        expect(
          notificationFeinQuestionWrapper(wrapper)
            .parents("ConditionalContent")
            .prop("visible")
        ).toBeFalsy();
      });
    });

    describe("when claim has existing employment status", () => {
      it("submits status and FEIN without changing fields", () => {
        const test = new MockBenefitsApplicationBuilder().employed().create();
        const { appLogic, claim, submitForm } = setup(test);

        submitForm();

        expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            employment_status: EmploymentStatus.employed,
            employer_fein: "12-3456789",
          }
        );
      });
    });
  });
});
