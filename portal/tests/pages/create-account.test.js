import { mount, shallow } from "enzyme";
import CreateAccount from "../../src/pages/create-account";
import React from "react";
import { act } from "react-dom/test-utils";
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
    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });

  describe("when the form is submitted", () => {
    it("calls createAccount", () => {
      const email = "email@test.com";
      const password = "TestP@ssw0rd!";

      changeField("username", email);
      changeField("password", password);
      submitForm();
      expect(appLogic.auth.createAccount).toHaveBeenCalledWith(email, password);
    });
  });

  it("redirects to '/' when claimantShowAuth is false", () => {
    process.env.featureFlags = { claimantShowAuth: false };
    appLogic = useAppLogic();
    act(() => {
      wrapper = mount(<CreateAccount appLogic={appLogic} />);
    });

    expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith("/");
  });

  it("does not redirect when claimantShowAuth is true", () => {
    process.env.featureFlags = { claimantShowAuth: true };
    appLogic = useAppLogic();
    act(() => {
      wrapper = mount(<CreateAccount appLogic={appLogic} />);
    });

    expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
  });

  it("displays employer-specific content when employerShowSelfRegistrationForm is false", () => {
    process.env.featureFlags = { employerShowSelfRegistrationForm: false };

    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });
});
