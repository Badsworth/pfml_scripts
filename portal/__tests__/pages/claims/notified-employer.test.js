import { simulateEvents, testHook } from "../../test-utils";
import Alert from "../../../src/components/Alert";
import Claim from "../../../src/models/Claim";
import ConditionalContent from "../../../src/components/ConditionalContent";
import { NotifiedEmployer } from "../../../src/pages/claims/notified-employer";
import QuestionPage from "../../../src/components/QuestionPage";
import React from "react";
import { act } from "react-dom/test-utils";
import routes from "../../../src/routes";
import { shallow } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("NotifiedEmployer", () => {
  let appLogic, changeField, changeRadioGroup, claim, wrapper;
  const application_id = "12345";

  function notificationDateQuestionWrapper() {
    return wrapper.find({ name: "leave_details.employer_notification_date" });
  }

  function mustNotifyWarningWrapper() {
    return wrapper.find(Alert);
  }

  beforeEach(() => {
    claim = new Claim({ application_id });
    const query = { claim_id: claim.application_id };
    testHook(() => {
      appLogic = useAppLogic();
    });
    act(() => {
      wrapper = shallow(
        <NotifiedEmployer claim={claim} query={query} appLogic={appLogic} />
      );
      ({ changeField, changeRadioGroup } = simulateEvents(wrapper));
    });
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
          .parents(ConditionalContent)
          .prop("visible")
      ).toBeTruthy();
    });
    it("hides must notify employer warning", () => {
      expect(
        mustNotifyWarningWrapper().parents(ConditionalContent).prop("visible")
      ).toBeFalsy();
    });
    describe("when user clicks continue", () => {
      it("calls updateClaim", () => {
        changeField("leave_details.employer_notification_date", "2020-06-25");
        act(() => {
          wrapper.find(QuestionPage).simulate("save");
        });
        expect(appLogic.updateClaim).toHaveBeenCalledWith(application_id, {
          leave_details: {
            employer_notified: true,
            employer_notification_date: "2020-06-25",
          },
        });
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
          .parents(ConditionalContent)
          .prop("visible")
      ).toBeFalsy();
    });
    it("shows must notify employer warning", () => {
      expect(
        mustNotifyWarningWrapper().parents(ConditionalContent).prop("visible")
      ).toBeTruthy();
    });
  });
  it("redirects to the checklist page", () => {
    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
      `${routes.claims.checklist}?claim_id=${claim.application_id}`
    );
  });
});
