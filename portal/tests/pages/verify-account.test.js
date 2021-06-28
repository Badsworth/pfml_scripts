import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import React from "react";
import VerifyAccount from "../../src/pages/verify-account";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import { simulateEvents } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/services/tracker");
jest.mock("../../src/hooks/useAppLogic");

describe("VerifyAccount", () => {
  let appLogic,
    changeField,
    click,
    resolveResendVerifyAccountCodeMock,
    submitForm,
    username,
    verificationCode,
    wrapper;

  function render() {
    act(() => {
      wrapper = shallow(<VerifyAccount appLogic={appLogic} />);
    });
    ({ changeField, click, submitForm } = simulateEvents(wrapper));
  }

  beforeEach(() => {
    appLogic = useAppLogic();
    appLogic.auth.resendVerifyAccountCode.mockImplementation(() => {
      return new Promise((resolve) => {
        resolveResendVerifyAccountCodeMock = resolve;
      });
    });

    username = "test@example.com";
    verificationCode = "123456";
    render();
  });

  it("renders the empty page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("submits empty strings if user has not entered values yet", async () => {
    await submitForm();

    expect(appLogic.auth.verifyAccount).toHaveBeenCalledWith("", "");
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

    it("calls verifyAccount when form is submitted", async () => {
      changeField("code", verificationCode);

      await submitForm();

      expect(appLogic.auth.verifyAccount).toHaveBeenCalledWith(
        username,
        verificationCode
      );
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

    it("calls verifyAccount when form is submitted", async () => {
      changeField("username", username);
      changeField("code", verificationCode);
      await submitForm();
      expect(appLogic.auth.verifyAccount).toHaveBeenCalledWith(
        username,
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
});
