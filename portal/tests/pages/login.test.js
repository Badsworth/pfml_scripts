import { simulateEvents, testHook } from "../test-utils";
import Login from "../../src/pages/login";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("Login", () => {
  let appLogic, changeField, query, submitForm, wrapper;

  function render(customProps = {}) {
    act(() => {
      wrapper = shallow(<Login appLogic={appLogic} query={query} />);
    });
    ({ changeField, submitForm } = simulateEvents(wrapper));
  }

  beforeEach(() => {
    query = {};
    testHook(() => {
      appLogic = useAppLogic();
    });
    render();
  });

  it("renders the empty page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when account-verified query param is true", () => {
    it("displays verification success message", () => {
      query = {
        "account-verified": "true",
      };
      render();
      const accountVerifiedMessageWrapper = wrapper.find({
        name: "account-verified-message",
      });
      expect(accountVerifiedMessageWrapper).toHaveLength(1);
      expect(accountVerifiedMessageWrapper).toMatchSnapshot();
    });
  });

  describe("when the form is submitted", () => {
    it("calls login", async () => {
      const email = "email@test.com";
      const password = "TestP@ssw0rd!";

      changeField("username", email);
      changeField("password", password);
      submitForm();
      expect(appLogic.auth.login).toHaveBeenCalledWith(email, password);
    });

    it("calls login with empty string when username is undefined", () => {
      const password = "TestP@ssw0rd!";

      submitForm();
      expect(appLogic.auth.login).toHaveBeenCalledWith("", "");

      changeField("password", password);
      submitForm();
      expect(appLogic.auth.login).toHaveBeenCalledWith("", password);
    });

    it("calls login with empty string when password is undefined", () => {
      const email = "email@test.com";

      submitForm();
      expect(appLogic.auth.login).toHaveBeenCalledWith("", "");

      changeField("username", email);
      submitForm();
      expect(appLogic.auth.login).toHaveBeenCalledWith(email, "");
    });
  });
});
