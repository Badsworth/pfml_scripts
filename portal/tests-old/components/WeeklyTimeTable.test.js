import React from "react";
import WeeklyTimeTable from "../../src/components/WeeklyTimeTable";
import { shallow } from "enzyme";

function render() {
  const days = [
    {
      day_of_week: "Sunday",
      minutes: 480,
    },
    {
      day_of_week: "Monday",
      minutes: 480,
    },
    {
      day_of_week: "Tuesday",
      minutes: 480,
    },
    {
      day_of_week: "Wednesday",
      minutes: 480,
    },
    {
      day_of_week: "Thursday",
      minutes: 480,
    },
    {
      day_of_week: "Friday",
      minutes: 480,
    },
    {
      day_of_week: "Saturday",
      minutes: 0,
    },
  ];
  const wrapper = shallow(<WeeklyTimeTable days={days} />);

  return wrapper;
}

describe("WeeklyTimeTable", () => {
  it("renders a table with days of the week and times", () => {
    const wrapper = render();

    expect(wrapper.find("Table")).toMatchSnapshot();
  });

  it("only renders hours if minutes are 0", () => {
    const wrapper = render();

    expect(wrapper.find("td").last().text()).toBe("0h");
  });
});
