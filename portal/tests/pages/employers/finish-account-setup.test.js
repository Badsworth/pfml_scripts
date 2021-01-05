import { simulateEvents, testHook } from "../../test-utils";
import FinishAccountSetup from "../../../src/pages/employers/finish-account-setup";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("FinishAccountSetup", () => {
  let appLogic, changeField, submitForm, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    act(() => {
      wrapper = shallow(<FinishAccountSetup appLogic={appLogic} />);
    });
    ({ changeField, submitForm } = simulateEvents(wrapper));
  });

  it("renders the page", () => {
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
