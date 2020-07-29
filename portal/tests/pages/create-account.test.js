import CreateAccount from "../../src/pages/create-account";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import { simulateEvents } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("CreateAccount", () => {
  let appLogic, changeField, submitForm, wrapper;

  beforeEach(() => {
    appLogic = useAppLogic();
    act(() => {
      wrapper = shallow(<CreateAccount appLogic={appLogic} />);
    });
    ({ changeField, submitForm } = simulateEvents(wrapper));
  });

  it("renders the empty page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is submitted", () => {
    it("calls createAccount", async () => {
      const email = "email@test.com";
      const password = "TestP@ssw0rd!";

      changeField("username", email);
      changeField("password", password);
      submitForm();
      expect(appLogic.auth.createAccount).toHaveBeenCalledWith(email, password);
    });

    it("calls createAccount with empty string when username is undefined", () => {
      const password = "TestP@ssw0rd!";

      submitForm();
      expect(appLogic.auth.createAccount).toHaveBeenCalledWith("", "");

      changeField("password", password);
      submitForm();
      expect(appLogic.auth.createAccount).toHaveBeenCalledWith("", password);
    });

    it("calls createAccount with empty string when password is undefined", () => {
      const email = "email@test.com";

      submitForm();
      expect(appLogic.auth.createAccount).toHaveBeenCalledWith("", "");

      changeField("username", email);
      submitForm();
      expect(appLogic.auth.createAccount).toHaveBeenCalledWith(email, "");
    });
  });
});
