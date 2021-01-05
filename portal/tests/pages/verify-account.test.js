import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import React from "react";
import VerifyAccount from "../../src/pages/verify-account";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import { simulateEvents } from "../test-utils";
import tracker from "../../src/services/tracker";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/services/tracker");
jest.mock("../../src/hooks/useAppLogic");

describe("VerifyAccount", () => {
  let appLogic,
    changeField,
    changeRadioGroup,
    click,
    ein,
    resolveResendVerifyAccountCodeMock,
    submitForm,
    username,
    verificationCode,
    wrapper;

  function render() {
    act(() => {
      wrapper = shallow(<VerifyAccount appLogic={appLogic} />);
    });
    ({ changeField, click, changeRadioGroup, submitForm } = simulateEvents(
      wrapper
    ));
  }

  beforeEach(() => {
    process.env.featureFlags = { claimantShowAuth: true };
    appLogic = useAppLogic();
    appLogic.auth.resendVerifyAccountCode.mockImplementation(() => {
      return new Promise((resolve) => {
        resolveResendVerifyAccountCodeMock = resolve;
      });
    });

    ein = "12-3456789";
    username = "test@example.com";
    verificationCode = "123456";
    render();
  });

  it("renders the empty page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("prevents submission when isEmployer isn't set when EIN fields are visible", async () => {
    await submitForm();

    expect(appLogic.setAppErrors).toHaveBeenCalledTimes(1);
    expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
      issueField: "isEmployer",
      issueType: "required",
    });

    expect(appLogic.auth.verifyAccount).not.toHaveBeenCalled();
    expect(appLogic.auth.verifyEmployerAccount).not.toHaveBeenCalled();

    changeRadioGroup("isEmployer", "false");
    await submitForm();

    expect(appLogic.auth.verifyAccount).toHaveBeenCalled();
  });

  it("submits empty strings if user has not entered values yet", async () => {
    changeRadioGroup("isEmployer", "true");
    await submitForm();

    expect(appLogic.auth.verifyEmployerAccount).toHaveBeenCalledWith(
      "",
      "",
      ""
    );
  });

  describe("when authData.username is set", () => {
    beforeEach(() => {
      appLogic.auth.authData = { createAccountUsername: username };
      render();
    });

    it("does not render an email field", () => {
      expect(wrapper.find("InputText[name='username']")).toHaveLength(0);
    });

    it("calls resendVerifyAccountCode when resend code button is clicked", () => {
      click({ name: "resend-code-button" });
      expect(appLogic.auth.resendVerifyAccountCode).toHaveBeenCalledWith(
        username
      );
    });

    describe("when user is not an employer and the form is submitted", () => {
      it("calls verifyAccount", async () => {
        changeField("code", verificationCode);
        changeRadioGroup("isEmployer", "false");

        await submitForm();
        expect(appLogic.auth.verifyAccount).toHaveBeenCalledWith(
          username,
          verificationCode
        );
      });
    });
  });

  describe("when authData.username is not set", () => {
    it("renders an email field", () => {
      expect(wrapper.find("InputText[name='username']")).toHaveLength(1);
    });

    it("calls resendVerifyAccountCode when resend code button is clicked", () => {
      changeField("username", username);
      click({ name: "resend-code-button" });
      expect(appLogic.auth.resendVerifyAccountCode).toHaveBeenCalledWith(
        username
      );
    });

    describe("when user is not an employer and the form is submitted", () => {
      it("calls verifyAccount", async () => {
        changeField("username", username);
        changeField("code", verificationCode);
        changeRadioGroup("isEmployer", "false");
        await submitForm();
        expect(appLogic.auth.verifyAccount).toHaveBeenCalledWith(
          username,
          verificationCode
        );
      });
    });
  });

  describe("when authData.employerIdNumber is set", () => {
    beforeEach(() => {
      appLogic.auth.authData = {
        createAccountUsername: username,
        createAccountFlow: "employer",
        employerIdNumber: ein,
      };
      render();
    });

    it("does not render a checkbox for user to state whether they're an employer", () => {
      expect(wrapper.find("InputChoiceGroup[name='isEmployer']").exists()).toBe(
        false
      );
    });

    it("calls verifyEmployerAccount upon form submission", async () => {
      changeField("code", verificationCode);
      await submitForm();
      expect(appLogic.auth.verifyEmployerAccount).toHaveBeenCalledWith(
        username,
        verificationCode,
        ein
      );
    });
  });

  describe("when employerIdNumber and createAccountFlow are not set in authData", () => {
    it("renders a checkbox for user to state whether they're an employer", () => {
      expect(wrapper.find("InputChoiceGroup[name='isEmployer']").exists()).toBe(
        true
      );
    });

    it("displays an employer id number field if user selects checkbox", () => {
      changeRadioGroup("isEmployer", "true");
      expect(wrapper.find("ConditionalContent").prop("visible")).toBe(true);
    });

    it("hides the employer id number field is user deselects checkbox", () => {
      changeRadioGroup("isEmployer", "false");
      expect(wrapper.find("ConditionalContent").prop("visible")).toBe(false);
    });

    it("calls verifyEmployerAccount upon form submission", async () => {
      changeRadioGroup("isEmployer", "true");
      changeField("code", verificationCode);
      changeField("username", username);
      changeField("ein", ein);
      await submitForm();
      expect(appLogic.auth.verifyEmployerAccount).toHaveBeenCalledWith(
        username,
        verificationCode,
        ein
      );
    });
  });

  describe("when authData.employerIdNumber is not set and createAccountFlow is 'claimant'", () => {
    beforeEach(() => {
      appLogic.auth.authData = {
        createAccountUsername: username,
        createAccountFlow: "claimant",
      };
      render();
    });

    it("does not render a checkbox for user to state whether they're an employer", () => {
      expect(wrapper.find("InputChoiceGroup[name='isEmployer']").exists()).toBe(
        false
      );
    });

    it("calls verifyAccount when form is submitted", async () => {
      changeField("code", verificationCode);
      await submitForm();

      expect(appLogic.auth.verifyAccount).toHaveBeenCalledWith(
        "test@example.com",
        verificationCode
      );
    });
  });

  it("shows success message after code is resent", async () => {
    click({ name: "resend-code-button" });
    await resolveResendVerifyAccountCodeMock();

    expect(wrapper.find("Alert[name='code-resent-message']")).toHaveLength(1);
    expect(wrapper.find("Alert[name='code-resent-message']")).toMatchSnapshot();
  });

  describe("when there are appErrors", () => {
    it("does not show success message when code is resent", async () => {
      appLogic.appErrors = new AppErrorInfoCollection([new AppErrorInfo()]);

      render();
      click({ name: "resend-code-button" });
      await resolveResendVerifyAccountCodeMock();

      expect(wrapper.find("Alert[name='code-resent-message']").exists()).toBe(
        false
      );
    });
  });

  describe("when claimantShowAuth flag is disabled", () => {
    beforeEach(() => {
      process.env.featureFlags = { claimantShowAuth: false };
      render();
    });

    it("render EIN field by default", () => {
      expect(wrapper.find("InputChoiceGroup[name='isEmployer']").exists()).toBe(
        false
      );
      expect(wrapper.find("ConditionalContent").prop("visible")).toBe(true);
    });
  });
});
