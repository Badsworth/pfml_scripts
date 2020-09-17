import React from "react";
import VerifyAccount from "../../src/pages/verify-account";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import { simulateEvents } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("VerifyAccount", () => {
  let appLogic,
    changeField,
    click,
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
    username = "test@example.com";
    verificationCode = "12345";
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

    describe("when resend code button is clicked", () => {
      it("calls resendVerifyAccountCode", () => {
        click({ name: "resend-code-button" });
        expect(appLogic.auth.resendVerifyAccountCode).toHaveBeenCalledWith(
          username
        );
      });
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

    describe("when resend code button is clicked", () => {
      it("calls resendVerifyAccountCode", () => {
        changeField("username", username);
        click({ name: "resend-code-button" });
        expect(appLogic.auth.resendVerifyAccountCode).toHaveBeenCalledWith(
          username
        );
      });
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
});
