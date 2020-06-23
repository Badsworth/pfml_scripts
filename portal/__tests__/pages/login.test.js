import Login from "../../src/pages/login";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import { simulateEvents } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("Login", () => {
  let appLogic, changeField, submitForm, wrapper;

  beforeEach(() => {
    appLogic = useAppLogic();
    act(() => {
      wrapper = shallow(<Login appLogic={appLogic} />);
    });
    ({ changeField, submitForm } = simulateEvents(wrapper));
  });

  it("renders the empty page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is submitted", () => {
    it("calls login", async () => {
      const email = "email@test.com";
      const password = "TestP@ssw0rd!";

      changeField("username", email);
      changeField("password", password);
      submitForm();
      expect(appLogic.login).toHaveBeenCalledWith(email, password);
    });

    it("calls login with empty string when username is undefined", () => {
      const password = "TestP@ssw0rd!";

      submitForm();
      expect(appLogic.login).toHaveBeenCalledWith("", "");

      changeField("password", password);
      submitForm();
      expect(appLogic.login).toHaveBeenCalledWith("", password);
    });

    it("calls login with empty string when password is undefined", () => {
      const email = "email@test.com";

      submitForm();
      expect(appLogic.login).toHaveBeenCalledWith("", "");

      changeField("username", email);
      submitForm();
      expect(appLogic.login).toHaveBeenCalledWith(email, "");
    });
  });
});
