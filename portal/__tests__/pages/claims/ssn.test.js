import { mount, shallow } from "enzyme";
import React from "react";
import Ssn from "../../../src/pages/claims/ssn";
import User from "../../../src/models/User";
import routes from "../../../src/routes";

describe("Ssn", () => {
  let setUser, user, wrapper;

  beforeEach(() => {
    user = new User();
    setUser = jest.fn();
    wrapper = shallow(<Ssn user={user} setUser={setUser} />);
  });

  it("renders the form", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("redirects to home if unrestrictedClaimFlow is not enabled", () => {
    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(routes.home);
  });

  it("redirects to leaveType if unrestrictedClaimFlow is enabled", () => {
    process.env = {
      ...process.env,
      featureFlags: {
        unrestrictedClaimFlow: true,
      },
    };
    wrapper = shallow(<Ssn user={user} setUser={setUser} />);

    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
      routes.claims.leaveType
    );
  });

  it("calls updateFieldFromEvent with user input", () => {
    wrapper = mount(<Ssn user={user} setUser={setUser} />);
    const inputData = {
      ssn: "555-55-5555",
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

  it("sets user state after successful save", async () => {
    await wrapper.find("QuestionPage").simulate("save");
    expect(setUser).toHaveBeenCalled();
  });
});
