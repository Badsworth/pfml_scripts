import "../../../src/i18n";
import EmployeeInfo from "../../../src/pages/eligibility/employee-info";
import React from "react";
import { shallow } from "enzyme";

describe("EmployeeInfo", () => {
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(<EmployeeInfo />);
  });

  it("renders the form", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("changes input value on user input", () => {
    const inputData = {
      firstName: "James",
      middleName: "AA",
      lastName: "Joyce",
      ssnOrItin: "222222222"
    };

    for (const key in inputData) {
      const value = inputData[key];
      const event = { target: { name: key, value } };
      wrapper.find({ name: key }).simulate("change", event);

      expect(wrapper.find({ name: key }).prop("value")).toEqual(value);
    }
  });
});
