import React from "react";
import { WorkPattern } from "../../src/models/Claim";
import WorkPatternTable from "../../src/components/WorkPatternTable";
import { shallow } from "enzyme";

describe("WorkPatternTable", () => {
  it("renders a WeeklyTimeTable with the work pattern's first week of minutes", () => {
    const weeklyMinutes = 8 * 60 * 7;
    let workPattern = WorkPattern.addWeek(new WorkPattern(), weeklyMinutes);
    workPattern = WorkPattern.addWeek(workPattern, weeklyMinutes);

    const wrapper = shallow(<WorkPatternTable weeks={workPattern.weeks} />);

    expect(wrapper).toMatchSnapshot();
  });
});
