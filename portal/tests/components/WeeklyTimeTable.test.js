import React from "react";
import WeeklyTimeTable from "../../src/components/WeeklyTimeTable";
import { range } from "lodash";
import { shallow } from "enzyme";

function render(weeks) {
  const wrapper = shallow(<WeeklyTimeTable weeks={weeks} />);

  return wrapper;
}

describe("WeeklyTimeTable", () => {
  it("renders day names in the header", () => {
    const wrapper = render([range(7)]);

    expect(wrapper.find("thead")).toMatchSnapshot();
  });

  it("renders a row for each week", () => {
    const wrapper = render([range(7), range(7)]);

    expect(wrapper.find("tbody tr")).toHaveLength(2);
  });

  it("hides minutes from the time if minutes are 0", () => {
    const wrapper = render([[0, 15, 60, 75, 90, 105, 120]]);

    expect(wrapper.find("tbody")).toMatchSnapshot();
  });
});
