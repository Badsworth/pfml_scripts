import { simulateEvents, testHook } from "../test-utils";
import Login from "../../src/pages/login";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("Login", () => {
  const email = "email@test.com";
  const password = "TestP@ssw0rd!";
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

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();

    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
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

  describe("when session-timed-out query param is true", () => {
    it("displays session timed out info message", () => {
      query = {
        "session-timed-out": "true",
      };
      render();
      const sessionTimedOutMessageWrapper = wrapper.find({
        name: "session-timed-out-message",
      });
      expect(sessionTimedOutMessageWrapper).toHaveLength(1);
      expect(sessionTimedOutMessageWrapper).toMatchSnapshot();
    });
  });

  describe("when the form is submitted", () => {
    it("calls login", async () => {
      changeField("username", email);
      changeField("password", password);

      await submitForm();

      expect(appLogic.auth.login).toHaveBeenCalledWith(email, password);
    });

    it("calls login with query param", async () => {
      const nextPage = "/next-page";
      query = {
        next: nextPage,
      };
      render();
      changeField("username", email);
      changeField("password", password);

      await submitForm();

      expect(appLogic.auth.login).toHaveBeenCalledWith(
        email,
        password,
        nextPage
      );
    });
  });
});
