import { renderWithAppLogic, simulateEvents } from "../../test-utils";
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
      changeRadioGroup("employment_status", "employed");
    });

    it("shows FEIN question", () => {
      expect(
        notificationFeinQuestionWrapper()
          .parents("ConditionalContent")
          .prop("visible")
      ).toBeTruthy();
    });

    describe("when user clicks continue", () => {
      it("calls updateClaim", () => {
        const testFein = 987654;
        changeField("employer_fein", testFein);
        act(() => {
          wrapper.find("QuestionPage").simulate("save");
        });

        expect(appLogic.updateClaim).toHaveBeenCalledWith(
          claim.application_id,
          {
            employment_status: "employed",
            employer_fein: testFein,
          }
        );
      });
    });
  });

  describe("when user selects self-employed as their employment status", () => {
    beforeEach(() => {
      changeRadioGroup("employment_status", "self-employed");
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
      changeRadioGroup("employment_status", "unemployed");
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
