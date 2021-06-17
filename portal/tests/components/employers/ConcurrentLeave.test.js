import AmendableConcurrentLeave from "../../../src/components/employers/AmendableConcurrentLeave";
import ConcurrentLeave from "../../../src/components/employers/ConcurrentLeave";
import ConcurrentLeaveModel from "../../../src/models/ConcurrentLeave";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

describe("ConcurrentLeave", () => {
  let appLogic;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
  });

  it("renders the component", () => {
    const concurrentLeave = new ConcurrentLeaveModel({
      leave_start_date: "2020-03-01",
      leave_end_date: "2020-03-06",
    });
    const wrapper = shallow(
      <ConcurrentLeave
        appErrors={appLogic.appErrors}
        concurrentLeave={concurrentLeave}
        onChange={() => {}}
      />
    );

    expect(wrapper).toMatchSnapshot();
  });

  it("displays 'None reported' if no leave periods are reported", () => {
    const wrapper = shallow(
      <ConcurrentLeave
        appErrors={appLogic.appErrors}
        concurrentLeaves={[]}
        onChange={() => {}}
      />
    );

    expect(wrapper.find(AmendableConcurrentLeave).exists()).toEqual(false);
    expect(wrapper.find("th").last().text()).toEqual("None reported");
  });
});
