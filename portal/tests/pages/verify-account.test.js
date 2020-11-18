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
    submitForm,
    username,
    verificationCode,
    wrapper;

  function render() {
    act(() => {
      wrapper = shallow(<VerifyAccount appLogic={appLogic} />);
    });
    ({ changeField, click, changeCheckbox, submitForm } = simulateEvents(
      wrapper
    ));
  }

  beforeEach(() => {
    appLogic = useAppLogic();
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

    describe("when resend code button is clicked", () => {
      let resolveResendVerifyAccountCodeMock;
      beforeEach(() => {
        appLogic.auth.resendVerifyAccountCode.mockImplementation(() => {
          return new Promise((resolve) => {
            resolveResendVerifyAccountCodeMock = resolve;
          });
        });
      });

      it("calls resendVerifyAccountCode", () => {
        click({ name: "resend-code-button" });
        expect(appLogic.auth.resendVerifyAccountCode).toHaveBeenCalledWith(
          username
        );
      });

      it("shows success message after request completes", async () => {
        click({ name: "resend-code-button" });
        await resolveResendVerifyAccountCodeMock();
        expect(wrapper.find("Alert[name='code-resent-message']")).toHaveLength(
          1
        );
        expect(
          wrapper.find("Alert[name='code-resent-message']")
        ).toMatchSnapshot();
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
});
