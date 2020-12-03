import LeaveDatesAlert from "../../src/components/LeaveDatesAlert";
import React from "react";
import { shallow } from "enzyme";

describe("LeaveDatesAlert", () => {
  it("renders Alert with given dates", () => {
    const wrapper = shallow(
      <LeaveDatesAlert startDate="2021-01-01" endDate="2021-01-30" />
    );

    expect(wrapper).toMatchSnapshot();
  });

  it("renders Alert with custom headingLevel", () => {
    const wrapper = shallow(
      <LeaveDatesAlert
        startDate="2021-01-01"
        endDate="2021-01-30"
        headingLevel="3"
      />
    );

    expect(wrapper.find("Alert").prop("headingLevel")).toBe("3");
  });

  it("is empty render when one of the dates is missing", () => {
    const wrapper = shallow(<LeaveDatesAlert startDate="2021-01-01" />);

    expect(wrapper.isEmptyRender()).toBe(true);
  });
});
