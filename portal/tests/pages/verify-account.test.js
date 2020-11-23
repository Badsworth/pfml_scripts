import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import React from "react";
import VerifyAccount from "../../src/pages/verify-account";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import { simulateEvents } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("VerifyAccount", () => {
  let appLogic,
    changeCheckbox,
    changeField,
    click,
    ein,
    resolveResendVerifyAccountCodeMock,
    submitForm,
    username,
    verificationCode,
    wrapper;

  function render(query = {}) {
    act(() => {
      wrapper = shallow(<VerifyAccount appLogic={appLogic} query={query} />);
    });
    ({ changeField, click, changeCheckbox, submitForm } = simulateEvents(
      wrapper
    ));
  }

  beforeEach(() => {
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

    describe("when the form is submitted", () => {
      it("calls verifyAccount", () => {
        changeField("code", verificationCode);
        submitForm();
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

    describe("when the form is submitted", () => {
      it("calls verifyAccount", () => {
        changeField("username", username);
        changeField("code", verificationCode);
        submitForm();
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
      expect(wrapper.find("InputChoice[name='isEmployer']").exists()).toBe(
        false
      );
    });

    it("calls verifyEmployerAccount upon form submission", () => {
      changeField("code", verificationCode);
      submitForm();
      expect(appLogic.auth.verifyEmployerAccount).toHaveBeenCalledWith(
        username,
        verificationCode,
        ein
      );
    });
  });

  describe("when employerIdNumber and createAccountFlow are not set in authData", () => {
    it("renders a checkbox for user to state whether they're an employer", () => {
      expect(wrapper.find("InputChoice[name='isEmployer']").exists()).toBe(
        true
      );
    });

    it("displays an employer id number field if user selects checkbox", () => {
      changeCheckbox("isEmployer", true);
      expect(wrapper.find("ConditionalContent").prop("visible")).toBe(true);
    });

    it("hides the employer id number field is user deselects checkbox", () => {
      changeCheckbox("isEmployer", false);
      expect(wrapper.find("ConditionalContent").prop("visible")).toBe(false);
    });

    it("calls verifyEmployerAccount upon form submission", () => {
      changeCheckbox("isEmployer", true);
      changeField("code", verificationCode);
      changeField("username", username);
      changeField("ein", ein);
      submitForm();
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
      expect(wrapper.find("InputChoice[name='isEmployer']").exists()).toBe(
        false
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

  describe("when query includes user-not-found", () => {
    beforeEach(() => {
      render({ "user-not-found": "true" });
    });

    it("renders info alert", () => {
      expect(wrapper.find("Alert[name='user-not-found-message']")).toHaveLength(
        1
      );
      expect(
        wrapper.find("Alert[name='user-not-found-message']")
      ).toMatchSnapshot();
    });

    it("initially hides the lead text and code field", () => {
      expect(wrapper.find("Lead").exists()).toBe(false);
      expect(wrapper.find("InputText[name='code']").exists()).toBe(false);
    });

    it("initially uses primary styling for resend code button", () => {
      // no variation means it's rendered as a primary button
      expect(
        wrapper.find({ name: "resend-code-button" }).prop("variation")
      ).toBeNull();
    });

    it("hides info alert when code is resent", async () => {
      click({ name: "resend-code-button" });
      await resolveResendVerifyAccountCodeMock();

      expect(wrapper.find("Alert[name='code-resent-message']")).toHaveLength(1);
    });

    it("shows lead text and code field when code is resent", async () => {
      click({ name: "resend-code-button" });
      await resolveResendVerifyAccountCodeMock();

      expect(wrapper.find("Lead").exists()).toBe(true);
      expect(wrapper.find("InputText[name='code']").exists()).toBe(true);
    });
  });
});
