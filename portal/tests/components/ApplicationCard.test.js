import ApplicationCard from "../../src/components/ApplicationCard";
import Claim from "../../src/models/Claim";
import { MockClaimBuilder } from "../test-utils";
import React from "react";
import { shallow } from "enzyme";

describe("ApplicationCard", () => {
  it("renders a card for the given application", () => {
    const claimAttrs = new MockClaimBuilder().create();

    const wrapper = shallow(
      <ApplicationCard claim={new Claim(claimAttrs)} number={2} />
    );

    expect(wrapper).toMatchSnapshot();
  });

  it("renders Continuous leave period date range", () => {
    const claimAttrs = new MockClaimBuilder().continuous().create();

    const wrapper = shallow(
      <ApplicationCard claim={new Claim(claimAttrs)} number={2} />
    );
    const leavePeriodHeading = wrapper
      .find("Heading")
      .filterWhere(
        (heading) => heading.children().text() === "Continuous leave"
      );

    expect(leavePeriodHeading.exists()).toBe(true);
    expect(wrapper.html()).toMatch("1/1/2021 – 6/1/2021");
  });

  it("renders Reduced Schedule leave period date range", () => {
    const claimAttrs = new MockClaimBuilder().reducedSchedule().create();

    const wrapper = shallow(
      <ApplicationCard claim={new Claim(claimAttrs)} number={2} />
    );
    const leavePeriodHeading = wrapper
      .find("Heading")
      .filterWhere(
        (heading) => heading.children().text() === "Reduced leave schedule"
      );

    expect(leavePeriodHeading.exists()).toBe(true);
    expect(wrapper.html()).toMatch("2/1/2021 – 7/1/2021");
  });

  it("renders Intermittent leave period date range", () => {
    const claimAttrs = new MockClaimBuilder().intermittent().create();

    const wrapper = shallow(
      <ApplicationCard claim={new Claim(claimAttrs)} number={2} />
    );
    const leavePeriodHeading = wrapper
      .find("Heading")
      .filterWhere(
        (heading) => heading.children().text() === "Intermittent leave"
      );

    expect(leavePeriodHeading.exists()).toBe(true);
    expect(wrapper.html()).toMatch("2/1/2021 – 7/1/2021");
  });

  describe("when the claim status is Submitted", () => {
    let claimAttrs, wrapper;

    beforeEach(() => {
      claimAttrs = new MockClaimBuilder().submitted().create();
      wrapper = shallow(
        <ApplicationCard claim={new Claim(claimAttrs)} number={2} />
      );
    });

    it("includes a link to edit the claim", () => {
      expect(wrapper.find("ButtonLink")).toHaveLength(1);
    });

    it("uses the Case ID as the main heading", () => {
      expect(wrapper.find("Heading[level='2']").children().text()).toBe(
        claimAttrs.fineos_absence_id
      );
    });
  });

  describe("when the claim status is Completed", () => {
    let wrapper;

    beforeEach(() => {
      const claimAttrs = new MockClaimBuilder().completed().create();

      wrapper = shallow(
        <ApplicationCard claim={new Claim(claimAttrs)} number={2} />
      );
    });

    it("does not include a link to edit the claim", () => {
      expect(wrapper.find("ButtonLink")).toHaveLength(0);
    });
  });
});
