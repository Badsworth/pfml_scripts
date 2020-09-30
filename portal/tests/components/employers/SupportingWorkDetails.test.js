import {
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
} from "../../../src/models/Claim";
import React from "react";
import ReviewRow from "../../../src/components/ReviewRow";
import SupportingWorkDetails from "../../../src/components/employers/SupportingWorkDetails";
import { shallow } from "enzyme";

describe("SupportingWorkDetails", () => {
  let leavePeriods, wrapper;

  beforeEach(() => {
    leavePeriods = [
      new IntermittentLeavePeriod({
        leave_period_id: 3,
        duration: 3,
        duration_basis: DurationBasis.hours,
        frequency: 6,
        frequency_interval: 6,
        frequency_interval_basis: FrequencyIntervalBasis.months,
      }),
    ];
    wrapper = shallow(
      <SupportingWorkDetails intermittentLeavePeriods={leavePeriods} />
    );
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("has a ReviewRow that takes in an AmendButton", () => {
    expect(
      wrapper.find(ReviewRow).first().render().find(".amend-text").text()
    ).toEqual("Amend");
  });

  it("renders weekly hours", () => {
    expect(wrapper.find("p").first().text()).toEqual(
      leavePeriods[0].duration.toString()
    );
  });
});
