import { simulateEvents, testHook } from "../test-utils";
import React from "react";
import ResetPassword from "../../src/pages/reset-password";
import { shallow } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/hooks/useAppLogic");

describe("ResetPassword", () => {
  let appLogic, resolveResendCodeMock;

  function render(customProps = {}) {
    const props = Object.assign(
      {
        appLogic,
        query: {},
      },
      customProps
    );

    return shallow(<ResetPassword {...props} />);
  }

  beforeEach(() => {
    process.env.featureFlags = { claimantShowAuth: true };

    testHook(() => {
      appLogic = useAppLogic();
    });

    appLogic.auth.resendForgotPasswordCode.mockImplementation(() => {
      return new Promise((resolve) => {
        resolveResendCodeMock = resolve;
      });
    });
  });

  it("renders form", () => {
    const wrapper = render();

    expect(wrapper).toMatchSnapshot();
  });

  describe("when authData.username is set", () => {
    const username = "test@example.com";

    beforeEach(() => {
      appLogic.auth.authData = { resetPasswordUsername: username };
    });

    it("does not render an email field", () => {
      const wrapper = render();

      expect(wrapper.find("InputText[name='username']")).toHaveLength(0);
    });

    describe("when the form is submitted", () => {
      it("calls resetPassword", () => {
        const password = "abcdef12345678";
        const code = "123456";
        const wrapper = render();
        const { changeField, submitForm } = simulateEvents(wrapper);

        changeField("code", code);
        changeField("password", password);
        submitForm();

        expect(appLogic.auth.resetPassword).toHaveBeenCalledWith(
          username,
          code,
          password
        );
      });
    });
  });

  describe("when authData.username is not set", () => {
    it("render an email field", () => {
      const wrapper = render();

      expect(wrapper.find("InputText[name='username']")).toHaveLength(1);
    });

    describe("when the form is submitted", () => {
      it("calls resetPassword", () => {
        const email = "email@test.com";
        const password = "abcdef12345678";
        const code = "123456";
        const wrapper = render();
        const { changeField, submitForm } = simulateEvents(wrapper);

        changeField("code", code);
        changeField("password", password);
        changeField("username", email);
        submitForm();

        expect(appLogic.auth.resetPassword).toHaveBeenCalledWith(
          email,
          code,
          password
        );
      });
    });
  });

  describe("when query includes user-not-found", () => {
    let wrapper;

    beforeEach(() => {
      wrapper = render({ query: { "user-not-found": "true" } });
    });

    it("renders different title and lead text, and initially hides all fields except for email", () => {
      expect(wrapper).toMatchSnapshot();
    });

    it("initially uses primary styling for resend code button", () => {
      // no variation means it's rendered as a primary button
      expect(
        wrapper.find({ name: "resend-code-button" }).prop("variation")
      ).toBeNull();
    });

    it("hides info alert when code is resent", async () => {
      const { click } = simulateEvents(wrapper);

      click({ name: "resend-code-button" });
      await resolveResendCodeMock();

      expect(wrapper.find("Alert[name='code-resent-message']")).toHaveLength(1);
    });

    it("shows lead text and code field when code is resent", async () => {
      const { click } = simulateEvents(wrapper);

      click({ name: "resend-code-button" });
      await resolveResendCodeMock();

      expect(wrapper.find("Lead").exists()).toBe(true);
      expect(wrapper.find("InputText[name='code']").exists()).toBe(true);
    });

    it("prevents submission when isEmployer isn't set", async () => {
      const {
        changeField,
        changeRadioGroup,
        click,
        submitForm,
      } = simulateEvents(wrapper);

      // Get page into a submittable state
      changeField("username", "foo@example.com");
      click({ name: "resend-code-button" });
      await resolveResendCodeMock();

      submitForm();

      expect(appLogic.setAppErrors).toHaveBeenCalledTimes(1);
      expect(appLogic.auth.resetPassword).not.toHaveBeenCalled();
      expect(
        appLogic.auth.resetEmployerPasswordAndCreateEmployerApiAccount
      ).not.toHaveBeenCalled();

      changeRadioGroup("isEmployer", "false");
      submitForm();

      expect(appLogic.auth.resetPassword).not.toHaveBeenCalled();
    });

    it("calls resetEmployerPasswordAndCreateEmployerApiAccount when user indicates they're an employer", async () => {
      const {
        changeRadioGroup,
        changeField,
        click,
        submitForm,
      } = simulateEvents(wrapper);

      const email = "email@test.com";
      const password = "abcdef12345678";
      const code = "123456";
      const ein = "12-3456789";

      // Get page into a submittable state
      changeField("username", email);
      click({ name: "resend-code-button" });
      await resolveResendCodeMock();

      // Fill out the remaining fields
      changeField("code", code);
      changeField("password", password);
      changeRadioGroup("isEmployer", "true");
      changeField("ein", ein);

      submitForm();

      expect(
        appLogic.auth.resetEmployerPasswordAndCreateEmployerApiAccount
      ).toHaveBeenCalledWith(email, code, password, ein);
    });

    it("calls resetPassword when user doesn't indicate they're an employer", async () => {
      const {
        changeField,
        changeRadioGroup,
        click,
        submitForm,
      } = simulateEvents(wrapper);

      const email = "email@test.com";
      const password = "abcdef12345678";
      const code = "123456";

      // Get page into a submittable state
      changeField("username", email);
      click({ name: "resend-code-button" });
      await resolveResendCodeMock();

      // Fill out the remaining fields
      changeField("code", code);
      changeField("password", password);
      changeRadioGroup("isEmployer", "false");

      submitForm();

      expect(appLogic.auth.resetPassword).toHaveBeenCalledWith(
        email,
        code,
        password
      );
    });
  });

  describe("when claimantShowAuth flag is disabled", () => {
    let wrapper;

    beforeEach(() => {
      process.env.featureFlags = { claimantShowAuth: false };
      wrapper = render({ query: { "user-not-found": "true" } });
    });

    it("render EIN field by default", async () => {
      const { changeField, click } = simulateEvents(wrapper);

      // Get page into a submittable state
      changeField("username", "foo@example.com");
      click({ name: "resend-code-button" });
      await resolveResendCodeMock();

      expect(wrapper.find("InputChoiceGroup[name='isEmployer']").exists()).toBe(
        false
      );
      expect(wrapper.find("ConditionalContent").prop("visible")).toBe(true);
    });
  });
});
