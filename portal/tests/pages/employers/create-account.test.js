import CreateAccount from "../../../src/pages/employers/create-account";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import { simulateEvents } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("CreateAccount", () => {
  let appLogic, changeField, submitForm, wrapper;

  beforeEach(() => {
    appLogic = useAppLogic();
    process.env.featureFlags = {
      employerShowSelfRegistrationForm: true,
    };
    act(() => {
      wrapper = shallow(<CreateAccount appLogic={appLogic} />);
    });
    ({ changeField, submitForm } = simulateEvents(wrapper));
  });

  describe("when employerShowSelfRegistrationForm is set to true", () => {
    it("renders the page", () => {
      expect(wrapper).toMatchSnapshot();
      wrapper.find("Trans").forEach((trans) => {
        expect(trans.dive()).toMatchSnapshot();
      });
    });

    it("displays the form fields", () => {
      expect(wrapper.find("InputText").length).toEqual(2);
      expect(wrapper.find("InputPassword").length).toEqual(1);
    });

    it("calls createAccount upon form submission", async () => {
      const email = "email@test.com";
      const password = "TestP@ssw0rd!";
      const ein = "123456789";

      changeField("username", email);
      changeField("password", password);
      changeField("ein", ein);
      await submitForm();
      expect(appLogic.auth.createEmployerAccount).toHaveBeenCalledWith(
        email,
        password,
        ein
      );
    });
  });

  describe("when employerShowSelfRegistrationForm is set to false", () => {
    it("does not display the form fields", () => {
      process.env.featureFlags = {
        employerShowSelfRegistrationForm: false,
      };

      let wrapper;
      act(() => {
        wrapper = shallow(<CreateAccount appLogic={appLogic} />);
      });

      expect(wrapper.find("InputText").length).toEqual(0);
      expect(wrapper.find("InputPassword").length).toEqual(0);
    });
  });

  it("renders pre-launch content when claimantShowMedicalLeaveType is false", () => {
    process.env.featureFlags = {
      claimantShowMedicalLeaveType: false,
    };

    wrapper = shallow(<CreateAccount appLogic={appLogic} />);

    expect(wrapper).toMatchSnapshot();
    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });

  it("renders post-launch content when claimantShowMedicalLeaveType is true", () => {
    process.env.featureFlags = {
      claimantShowMedicalLeaveType: true,
    };

    wrapper = shallow(<CreateAccount appLogic={appLogic} />);

    expect(wrapper).toMatchSnapshot();
    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });
});
