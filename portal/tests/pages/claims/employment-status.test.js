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

  beforeEach(() => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(EmploymentStatusPage));
    ({ changeField, changeRadioGroup } = simulateEvents(wrapper));
  });

  it("renders the page", () => {
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

    describe("when user clicks continue", () => {
      it("calls claims.update", () => {
        const testFein = 987654;
        changeField("employer_fein", testFein);
        act(() => {
          wrapper.find("QuestionPage").simulate("save");
        });

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            employment_status: EmploymentStatus.employed,
            employer_fein: testFein,
          },
          expect.any(Array)
        );
      });
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
