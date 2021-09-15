import { simulateEvents, testHook } from "../test-utils";
import ForgotPassword from "../../src/pages/forgot-password";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("ForgotPassword", () => {
  let appLogic, changeField, submitForm, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    act(() => {
      wrapper = shallow(<ForgotPassword appLogic={appLogic} />);
    });
    ({ changeField, submitForm } = simulateEvents(wrapper));
  });

  it("renders form", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is submitted", () => {
    it("calls forgotPassword", async () => {
      const email = "email@test.com";

      changeField("username", email);
      await submitForm();
      expect(appLogic.auth.forgotPassword).toHaveBeenCalledWith(email);
    });
  });
});
