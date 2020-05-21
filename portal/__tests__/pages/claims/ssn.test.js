import { mount, shallow } from "enzyme";
import React from "react";
import Ssn from "../../../src/pages/claims/ssn";
import User from "../../../src/models/User";
import routes from "../../../src/routes";
import usersApi from "../../../src/api/usersApi";

jest.mock("../../../src/api/usersApi");
const claim_id = "12345";

const render = (props = {}, mountComponent) => {
  const commonProps = {
    user: new User(),
    setUser: jest.fn(),
    query: { claim_id },
  };

  const renderFn = mountComponent ? mount : shallow;

  return renderFn(<Ssn {...commonProps} {...props} />);
};

describe("Ssn", () => {
  let wrapper;

  beforeEach(() => {
    wrapper = render();
  });

  it("renders the form", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("redirects to success page if unrestrictedClaimFlow is not enabled", () => {
    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
      routes.claims.success
    );
  });

  it("redirects to leaveType if unrestrictedClaimFlow is enabled", () => {
    process.env = {
      ...process.env,
      featureFlags: {
        unrestrictedClaimFlow: true,
      },
    };
    wrapper = render();

    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
      `${routes.claims.leaveType}?claim_id=${claim_id}`
    );
  });

  it("calls updateFieldFromEvent with user input", () => {
    wrapper = render({}, true);
    const inputData = {
      ssn_or_itin: "555-55-5555",
    };

    for (const key in inputData) {
      const value = inputData[key];
      const event = { target: { name: key, value } };
      wrapper.find({ name: key, type: "text" }).simulate("change", event);
      expect(wrapper.find({ name: key, type: "text" }).prop("value")).toEqual(
        value
      );
    }
  });

  describe("when the form is successfully submitted", () => {
    it("calls updateUser and updates the state", async () => {
      expect.assertions();
      const setUser = jest.fn();

      wrapper = render({ setUser });

      await wrapper.find("QuestionPage").simulate("save");

      expect(usersApi.updateUser).toHaveBeenCalledTimes(1);
      expect(setUser).toHaveBeenCalledWith(expect.any(User));
    });
  });
});
