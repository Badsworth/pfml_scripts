import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import NotifiedEmployer from "../../../src/pages/applications/notified-employer";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = {}) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(NotifiedEmployer, {
    claimAttrs,
  });

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

describe("NotifiedEmployer", () => {
  function notificationDateQuestionWrapper(wrapper) {
    return wrapper.find({ name: "leave_details.employer_notification_date" });
  }

  function mustNotifyWarningWrapper(wrapper) {
    return wrapper.find("Alert[state='warning']");
  }

  it("renders the page", () => {
    const { wrapper } = setup();
    expect(wrapper).toMatchSnapshot();
  });

  it("shows employer notification date question when user selects yes to having notified employer", () => {
    const { changeRadioGroup, wrapper } = setup();

    changeRadioGroup("leave_details.employer_notified", "true");

    expect(
      notificationDateQuestionWrapper(wrapper)
        .parents("ConditionalContent")
        .prop("visible")
    ).toBeTruthy();
  });

  it("hides must notify employer warning when user selects yes to having notified employer", () => {
    const { changeRadioGroup, wrapper } = setup();

    changeRadioGroup("leave_details.employer_notified", "true");

    expect(
      mustNotifyWarningWrapper(wrapper)
        .parents("ConditionalContent")
        .prop("visible")
    ).toBeFalsy();
  });

  it("calls claims.update when user submits form with newly entered data", () => {
    const { appLogic, changeField, changeRadioGroup, claim, submitForm } =
      setup();

    changeRadioGroup("leave_details.employer_notified", "true");
    changeField("leave_details.employer_notification_date", "2020-06-25");

    submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        leave_details: {
          employer_notified: true,
          employer_notification_date: "2020-06-25",
        },
      }
    );
  });

  it("calls claims.update when user submits form with previously entered data", () => {
    const { appLogic, claim, submitForm } = setup({
      leave_details: {
        employer_notified: true,
        employer_notification_date: "2020-06-25",
      },
    });

    submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        leave_details: {
          employer_notified: true,
          employer_notification_date: "2020-06-25",
        },
      }
    );
  });

  describe("when user selects no to having notified employer", () => {
    it("hides employer notification date question", () => {
      const { changeRadioGroup, wrapper } = setup();

      changeRadioGroup("leave_details.employer_notified", "false");

      expect(
        notificationDateQuestionWrapper(wrapper)
          .parents("ConditionalContent")
          .prop("visible")
      ).toBeFalsy();
    });

    it("shows must notify employer warning", () => {
      const { changeRadioGroup, wrapper } = setup();

      changeRadioGroup("leave_details.employer_notified", "false");

      expect(
        mustNotifyWarningWrapper(wrapper)
          .parents("ConditionalContent")
          .prop("visible")
      ).toBeTruthy();
    });
  });
});
