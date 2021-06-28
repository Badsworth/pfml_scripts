import ConcurrentLeave from "../../../src/components/employers/ConcurrentLeave";
import ConcurrentLeaveModel from "../../../src/models/ConcurrentLeave";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

const CONCURRENT_LEAVE = new ConcurrentLeaveModel({
  is_for_current_employer: true,
  leave_start_date: "2020-03-01",
  leave_end_date: "2020-03-06",
});

describe("ConcurrentLeave", () => {
  let appLogic;

  function render(providedProps) {
    const defaultProps = {
      addedConcurrentLeave: null,
      appErrors: appLogic.appErrors,
      concurrentLeave: CONCURRENT_LEAVE,
      onAdd: () => {},
      onChange: () => {},
      onRemove: () => {},
    };
    const componentProps = {
      ...defaultProps,
      ...providedProps,
    };
    return shallow(<ConcurrentLeave {...componentProps} />);
  }

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
  });

  it("renders the component", () => {
    const wrapper = render();
    expect(wrapper).toMatchSnapshot();
  });

  it("displays 'None reported' and the add button if no leave periods are reported", () => {
    const wrapper = render({ concurrentLeave: null });
    expect(wrapper.find("AmendableConcurrentLeave").exists()).toEqual(false);
    expect(wrapper.find("th").last().text()).toEqual("None reported");
    expect(wrapper.find("AddButton").exists()).toBe(true);
  });

  it("displays a row for claimant-submitted concurrent leave", () => {
    const wrapper = render();
    expect(wrapper.find("AmendableConcurrentLeave").length).toBe(1);
  });

  it("does not display the add button if there exists a claimant-submitted concurrent leave", () => {
    const wrapper = render();
    expect(wrapper.find("AddButton").exists()).toBe(false);
  });

  it("displays a row for admin-added concurrent leave", () => {
    const wrapper = render({
      addedConcurrentLeave: CONCURRENT_LEAVE,
      concurrentLeave: null,
    });

    expect(wrapper.find("AmendableConcurrentLeave").length).toBe(1);
  });

  it("does not display the add button if there exists an admin-added concurrent leave", () => {
    const wrapper = render({
      addedConcurrentLeave: CONCURRENT_LEAVE,
      concurrentLeave: null,
    });
    expect(wrapper.find("AddButton").exists()).toBe(false);
  });
});
