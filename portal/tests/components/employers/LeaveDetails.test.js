import LeaveDetails from "../../../src/components/employers/LeaveDetails";
import React from "react";
import ReviewRow from "../../../src/components/ReviewRow";
import { claim } from "../../test-utils";
import { shallow } from "enzyme";

describe("LeaveDetails", () => {
  let wrapper;

  beforeEach(() => {
    wrapper = shallow(<LeaveDetails claim={claim} />);
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("renders leave reason and application id", () => {
    expect(wrapper.find(ReviewRow).first().children().first().text()).toEqual(
      claim.leave_details.reason
    );
    expect(wrapper.find(ReviewRow).at(1).children().first().text()).toEqual(
      claim.application_id.toString()
    );
  });

  it("has a ReviewRow that takes an AmendLink as a prop", () => {
    expect(
      wrapper.find(ReviewRow).at(2).render().find("span.amend-text").text()
    ).toEqual("Amend");
  });

  it("renders formatted date range for leave duration", () => {
    expect(wrapper.find(ReviewRow).at(2).children().first().text()).toEqual(
      "1/1/2021"
    );
  });

  it("renders formatted employer notification date", () => {
    expect(wrapper.find(ReviewRow).last().children().first().text()).toEqual(
      "1/1/2021 – 6/1/2021"
    );
  });
});
