import { DayOfWeek, WorkPattern, WorkPatternDay } from "../../src/models/Claim";
import React from "react";
import WorkPatternTable from "../../src/components/WorkPatternTable";
import { shallow } from "enzyme";

function render(workPattern) {
  workPattern = workPattern || new WorkPattern();

  const wrapper = shallow(<WorkPatternTable weeks={workPattern.weeks} />);

  return wrapper;
}

describe("WorkPatternTable", () => {
  it("renders day names in the header", () => {
    const wrapper = render();

    expect(wrapper.find("thead")).toMatchSnapshot();
  });

  it("renders a row for each week in the WorkPattern", () => {
    // 8 hours days for 7 days
    const weeklyMinutes = 8 * 60 * 7;
    let workPattern = WorkPattern.addWeek(new WorkPattern(), weeklyMinutes);
    workPattern = WorkPattern.addWeek(workPattern, weeklyMinutes);

    const wrapper = render(workPattern);

    expect(wrapper.find("tbody tr")).toHaveLength(2);
  });

  it("hides minutes from the time if minutes are 0", () => {
    const workPattern = new WorkPattern({
      work_pattern_days: [
        new WorkPatternDay({
          day_of_week: DayOfWeek.sunday,
          minutes: 0,
          week_number: 1,
        }),
        new WorkPatternDay({
          day_of_week: DayOfWeek.monday,
          minutes: 15,
          week_number: 1,
        }),
        new WorkPatternDay({
          day_of_week: DayOfWeek.tuesday,
          minutes: 60,
          week_number: 1,
        }),
        new WorkPatternDay({
          day_of_week: DayOfWeek.wednesday,
          minutes: 75,
          week_number: 1,
        }),
        new WorkPatternDay({
          day_of_week: DayOfWeek.thursday,
          minutes: 90,
          week_number: 1,
        }),
        new WorkPatternDay({
          day_of_week: DayOfWeek.friday,
          minutes: 105,
          week_number: 1,
        }),
        new WorkPatternDay({
          day_of_week: DayOfWeek.saturday,
          minutes: 120,
          week_number: 1,
        }),
      ],
    });

    const wrapper = render(workPattern);

    expect(wrapper.find("tbody")).toMatchSnapshot();
  });
});
