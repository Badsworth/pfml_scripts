import React from "react";
import ReviewRow from "../../../src/components/ReviewRow";
import SupportingWorkDetails from "../../../src/components/employers/SupportingWorkDetails";
import { claim } from "../../test-utils";
import { shallow } from "enzyme";

describe("SupportingWorkDetails", () => {
  const leavePeriods = claim.leave_details.intermittent_leave_periods;
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(
      <SupportingWorkDetails intermittentLeavePeriods={leavePeriods} />
    );
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("has a ReviewRow that takes in an AmendLink", () => {
    expect(
      wrapper.find(ReviewRow).first().render().find("span.amend-text").text()
    ).toEqual("Amend");
  });

  it("renders weekly hours", () => {
    expect(wrapper.find("p").first().text()).toEqual(
      leavePeriods[0].duration.toString()
    );
  });
});
