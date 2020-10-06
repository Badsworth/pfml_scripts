import { simulateEvents, testHook } from "../../test-utils";
import React from "react";
import VerifyAccount from "../../../src/pages/employers/verify-account";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("VerifyAccount", () => {
  let appLogic, changeField, submitForm, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    act(() => {
      wrapper = shallow(<VerifyAccount appLogic={appLogic} />);
    });
    ({ changeField, submitForm } = simulateEvents(wrapper));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is submitted", () => {
    it("calls forgotPassword", () => {
      const email = "email@test.com";

      changeField("username", email);
      submitForm();
      expect(appLogic.auth.forgotPassword).toHaveBeenCalledWith(email);
    });
  });
});
