import LeaveDetails from "../../../src/components/employers/LeaveDetails";
import { MockEmployerClaimBuilder } from "../../test-utils";
import React from "react";
import ReviewRow from "../../../src/components/ReviewRow";
import { shallow } from "enzyme";

describe("LeaveDetails", () => {
  let claim, wrapper;

  beforeEach(() => {
    claim = new MockEmployerClaimBuilder().completed().create();
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

  it("renders formatted date range for leave duration", () => {
    expect(wrapper.find(ReviewRow).last().children().first().text()).toEqual(
      "1/1/2021 – 7/1/2021"
    );
  });
});
