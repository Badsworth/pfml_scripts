import { MockEmployerClaimBuilder, simulateEvents } from "../../test-utils";
import LeaveDetails from "../../../src/components/employers/LeaveDetails";
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

  it("does not render relationship question when claim is not for Care", () => {
    expect(wrapper.exists("InputChoiceGroup")).toBe(false);
  });

  it("renders the emergency regs content when claim is for Bonding", () => {
    const bondingClaim = new MockEmployerClaimBuilder()
      .completed()
      .bondingLeaveReason()
      .create();
    const bondingWrapper = shallow(<LeaveDetails claim={bondingClaim} />);

    expect(bondingWrapper.find("Details Trans").dive()).toMatchSnapshot();
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

  it("renders dash for leave duration if intermittent leave", () => {
    const claimWithIntermittentLeave = new MockEmployerClaimBuilder()
      .completed(true)
      .create();
    const wrapper = shallow(
      <LeaveDetails claim={claimWithIntermittentLeave} />
    );
    expect(wrapper.find(ReviewRow).last().children().first().text()).toEqual(
      "—"
    );
  });

  describe("Caring Leave", () => {
    const setup = () => {
      const onChangeBelieveRelationshipAccurateMock = jest.fn();
      const claim = new MockEmployerClaimBuilder()
        .completed()
        .caringLeaveReason()
        .create();
      const wrapper = shallow(
        <LeaveDetails
          claim={claim}
          onChangeBelieveRelationshipAccurate={
            onChangeBelieveRelationshipAccurateMock
          }
          onChangeRelationshipInaccurateReason={jest.fn()}
        />
      );
      const { changeRadioGroup } = simulateEvents(wrapper);
      return {
        changeRadioGroup,
        wrapper,
        onChangeBelieveRelationshipAccurateMock,
      };
    };

    it("does not render relationship question when showCaringLeaveType flag is false", () => {
      const { wrapper } = setup();
      expect(wrapper.exists("InputChoiceGroup")).toBe(false);
    });

    it("renders relationship question when showCaringLeaveType flag is true", () => {
      process.env.featureFlags = { showCaringLeaveType: true };
      const { wrapper } = setup();
      expect(wrapper).toMatchSnapshot();
      expect(wrapper.exists("InputChoiceGroup")).toBe(true);
    });

    it("initially renders with the comment box hidden", () => {
      const { wrapper } = setup();
      expect(wrapper.find("ConditionalContent").prop("visible")).toBe(false);
    });

    it("renders the comment box when user indicates the relationship is inaccurate ", () => {
      const {
        wrapper,
        changeRadioGroup,
        onChangeBelieveRelationshipAccurateMock,
      } = setup();
      changeRadioGroup("believeRelationshipAccurate", "no");
      expect(onChangeBelieveRelationshipAccurateMock).toHaveBeenCalledWith(
        "no"
      );
      wrapper.setProps({ believeRelationshipAccurate: "no" });
      expect(wrapper.find("ConditionalContent").prop("visible")).toBe(true);
    });
  });
});
