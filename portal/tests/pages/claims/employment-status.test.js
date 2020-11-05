import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import { EmploymentStatus } from "../../../src/models/Claim";
import EmploymentStatusPage from "../../../src/pages/claims/employment-status";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("EmploymentStatusPage", () => {
  let appLogic, changeField, changeRadioGroup, claim, wrapper;

  function notificationFeinQuestionWrapper() {
    return wrapper.find({ name: "employer_fein" });
  }

  describe("when claimantShowEmploymentStatus feature flag is disabled", () => {
    beforeEach(() => {
      process.env.featureFlags = {
        claimantShowEmploymentStatus: false,
      };
      ({ appLogic, claim, wrapper } = renderWithAppLogic(EmploymentStatusPage));
      ({ changeField, changeRadioGroup } = simulateEvents(wrapper));
    });

    it("renders the page without the employment status field", () => {
      expect(wrapper).toMatchSnapshot();
      expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    });

    it("submits status and FEIN", () => {
      const testFein = 123456789;
      changeField("employer_fein", testFein);

      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });

      expect(appLogic.claims.update).toHaveBeenCalledWith(
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
      ({ appLogic, claim, wrapper } = renderWithAppLogic(EmploymentStatusPage));
      ({ changeField, changeRadioGroup } = simulateEvents(wrapper));
    });

    it("renders the page with the employment status field", () => {
      expect(wrapper).toMatchSnapshot();
    });

    describe("when user selects employed in MA as their employment status", () => {
      beforeEach(() => {
        changeRadioGroup("employment_status", EmploymentStatus.employed);
      });

      it("shows FEIN question", () => {
        expect(
          notificationFeinQuestionWrapper()
            .parents("ConditionalContent")
            .prop("visible")
        ).toBeTruthy();
      });

      it("submits status and FEIN", () => {
        const testFein = 123456789;
        changeField("employer_fein", testFein);
        act(() => {
          wrapper.find("QuestionPage").simulate("save");
        });

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            employment_status: EmploymentStatus.employed,
            employer_fein: testFein,
          }
        );
      });
    });

    describe("when user selects self-employed as their employment status", () => {
      beforeEach(() => {
        changeRadioGroup("employment_status", EmploymentStatus.selfEmployed);
      });

      it("hides FEIN question", () => {
        expect(
          notificationFeinQuestionWrapper()
            .parents("ConditionalContent")
            .prop("visible")
        ).toBeFalsy();
      });

      it("submits status and empty FEIN", () => {
        act(() => {
          wrapper.find("QuestionPage").simulate("save");
        });

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            employment_status: EmploymentStatus.selfEmployed,
            employer_fein: null,
          }
        );
      });
    });

    describe("when user selects unemployed as their employment status", () => {
      beforeEach(() => {
        changeRadioGroup("employment_status", EmploymentStatus.unemployed);
      });
      it("hides FEIN question", () => {
        expect(
          notificationFeinQuestionWrapper()
            .parents("ConditionalContent")
            .prop("visible")
        ).toBeFalsy();
      });
    });
  });
});
