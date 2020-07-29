import { simulateEvents, testHook } from "../test-utils";
import React from "react";
import ResetPassword from "../../src/pages/reset-password";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("aws-amplify");

describe("ResetPassword", () => {
  let appLogic;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
  });

  it("renders form", () => {
    let wrapper;

    act(() => {
      wrapper = shallow(<ResetPassword appLogic={appLogic} />);
    });

    expect(wrapper).toMatchSnapshot();
  });

  describe("when authData.username is set", () => {
    const username = "test@example.com";

    beforeEach(() => {
      appLogic.auth.authData = { resetPasswordUsername: username };
    });

    it("does not render an email field", () => {
      let wrapper;

      act(() => {
        wrapper = shallow(<ResetPassword appLogic={appLogic} />);
      });

      expect(wrapper.find("InputText[name='username']")).toHaveLength(0);
    });

    describe("when the form is submitted", () => {
      it("calls resetPassword", async () => {
        const spy = jest.spyOn(appLogic.auth, "resetPassword");
        const password = "abcdef12345678";
        const code = "123456";
        let wrapper;

        act(() => {
          wrapper = shallow(<ResetPassword appLogic={appLogic} />);
        });
        const { changeField, submitForm } = simulateEvents(wrapper);

        changeField("code", code);
        changeField("password", password);
        submitForm();

        expect(spy).toHaveBeenCalledWith(username, code, password);
      });
    });
  });

  describe("when authData.username is not set", () => {
    it("render an email field", () => {
      let wrapper;

      act(() => {
        wrapper = shallow(<ResetPassword appLogic={appLogic} />);
      });

      expect(wrapper.find("InputText[name='username']")).toHaveLength(1);
    });

    describe("when the form is submitted", () => {
      it("calls resetPassword", async () => {
        const spy = jest.spyOn(appLogic.auth, "resetPassword");
        const email = "email@test.com";
        const password = "abcdef12345678";
        const code = "123456";
        let wrapper;

        act(() => {
          wrapper = shallow(<ResetPassword appLogic={appLogic} />);
        });
        const { changeField, submitForm } = simulateEvents(wrapper);

        changeField("code", code);
        changeField("password", password);
        changeField("username", email);
        submitForm();

        expect(spy).toHaveBeenCalledWith(email, code, password);
      });
    });
  });
});
