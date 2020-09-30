import LeaveDetails from "../../../src/components/employers/LeaveDetails";
import { MockClaimBuilder } from "../../test-utils";
import React from "react";
import ReviewRow from "../../../src/components/ReviewRow";
import { shallow } from "enzyme";

describe("LeaveDetails", () => {
  let claim, wrapper;

  beforeEach(() => {
    claim = new MockClaimBuilder().submitted().create();
    wrapper = shallow(<LeaveDetails claim={claim} />);
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("renders formatted leave reason as sentence case", () => {
    expect(wrapper.find(ReviewRow).first().children().first().text()).toEqual(
      "Medical leave"
    );
  });

  it("has a ReviewRow that takes an AmendButton as a prop", () => {
    expect(
      wrapper.find(ReviewRow).at(2).render().find(".amend-text").text()
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
