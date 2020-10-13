import {
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
} from "../../../src/models/Claim";
import IntermittentLeaveSchedule from "../../../src/components/employers/IntermittentLeaveSchedule";
import React from "react";
import { shallow } from "enzyme";

describe("IntermittentLeaveSchedule", () => {
  let wrapper;

  it("renders an irregular intermittent leave period", () => {
    const irregularIntermittentLeavePeriod = [
      new IntermittentLeavePeriod({
        leave_period_id: "mock-leave-period-id",
        start_date: "2021-02-01",
        end_date: "2021-07-01",
        duration: 3,
        duration_basis: DurationBasis.hours,
        frequency: 6,
        frequency_interval: 6,
        frequency_interval_basis: FrequencyIntervalBasis.months,
      }),
    ];

    wrapper = shallow(
      <IntermittentLeaveSchedule
        intermittentLeavePeriods={irregularIntermittentLeavePeriod}
      />
    );

    expect(wrapper).toMatchSnapshot();
  });

  it("renders a regular intermittent leave period", () => {
    const regularIntermittentLeavePeriods = [
      new IntermittentLeavePeriod({
        leave_period_id: "mock-leave-period-id",
        start_date: "2021-02-01",
        end_date: "2021-07-01",
        duration: 3,
        duration_basis: DurationBasis.hours,
        frequency: 2,
        frequency_interval: null,
        frequency_interval_basis: FrequencyIntervalBasis.weeks,
      }),
    ];

    wrapper = shallow(
      <IntermittentLeaveSchedule
        intermittentLeavePeriods={regularIntermittentLeavePeriods}
      />
    );

    expect(wrapper).toMatchSnapshot();
  });
});
