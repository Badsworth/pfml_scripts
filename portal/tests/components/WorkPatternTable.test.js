import React from "react";
import { WorkPattern } from "../../src/models/Claim";
import WorkPatternTable from "../../src/components/WorkPatternTable";
import { shallow } from "enzyme";

describe("WorkPatternTable", () => {
  it("renders a WeeklyTimeTable with the work pattern's week of minutes", () => {
    const weeklyMinutes = 8 * 60 * 7;
    const workPattern = WorkPattern.createWithWeek(weeklyMinutes);

    const wrapper = shallow(
      <WorkPatternTable days={workPattern.work_pattern_days} />
    );

    expect(wrapper).toMatchSnapshot();
  });
});
