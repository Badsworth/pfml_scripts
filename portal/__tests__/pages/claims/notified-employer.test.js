import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import NotifiedEmployer from "../../../src/pages/claims/notified-employer";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("NotifiedEmployer", () => {
  let appLogic, changeField, changeRadioGroup, claim, wrapper;

  function notificationDateQuestionWrapper() {
    return wrapper.find({ name: "leave_details.employer_notification_date" });
  }

  function mustNotifyWarningWrapper() {
    return wrapper.find("Alert[state='warning']");
  }

  beforeEach(() => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(NotifiedEmployer));
    ({ changeField, changeRadioGroup } = simulateEvents(wrapper));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when user selects yes to having notified employer", () => {
    beforeEach(() => {
      changeRadioGroup("leave_details.employer_notified", "true");
    });

    it("shows employer notification date question", () => {
      expect(
        notificationDateQuestionWrapper()
          .parents("ConditionalContent")
          .prop("visible")
      ).toBeTruthy();
    });

    it("hides must notify employer warning", () => {
      expect(
        mustNotifyWarningWrapper().parents("ConditionalContent").prop("visible")
      ).toBeFalsy();
    });

    describe("when user clicks continue", () => {
      it("calls updateClaim", () => {
        changeField("leave_details.employer_notification_date", "2020-06-25");
        act(() => {
          wrapper.find("QuestionPage").simulate("save");
        });

        expect(appLogic.updateClaim).toHaveBeenCalledWith(
          claim.application_id,
          {
            leave_details: {
              employer_notified: true,
              employer_notification_date: "2020-06-25",
            },
          }
        );
      });
    });
  });

  describe("when user selects no to having notified employer", () => {
    beforeEach(() => {
      changeRadioGroup("leave_details.employer_notified", "false");
    });

    it("hides employer notification date question", () => {
      expect(
        notificationDateQuestionWrapper()
          .parents("ConditionalContent")
          .prop("visible")
      ).toBeFalsy();
    });

    it("shows must notify employer warning", () => {
      expect(
        mustNotifyWarningWrapper().parents("ConditionalContent").prop("visible")
      ).toBeTruthy();
    });
  });
});
