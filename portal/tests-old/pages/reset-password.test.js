import { simulateEvents, testHook } from "../test-utils";
import React from "react";
import ResetPassword from "../../src/pages/reset-password";
import { shallow } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/hooks/useAppLogic");

describe("ResetPassword", () => {
  let appLogic;

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
    testHook(() => {
      appLogic = useAppLogic();
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
      it("calls resetPassword", async () => {
        const password = "abcdef12345678";
        const code = "123456";
        const wrapper = render();
        const { changeField, submitForm } = simulateEvents(wrapper);

        changeField("code", code);
        changeField("password", password);
        await submitForm();

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
      it("calls resetPassword", async () => {
        const email = "email@test.com";
        const password = "abcdef12345678";
        const code = "123456";
        const wrapper = render();
        const { changeField, submitForm } = simulateEvents(wrapper);

        changeField("code", code);
        changeField("password", password);
        changeField("username", email);
        await submitForm();

        expect(appLogic.auth.resetPassword).toHaveBeenCalledWith(
          email,
          code,
          password
        );
      });
    });
  });
});
