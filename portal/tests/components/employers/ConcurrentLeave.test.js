import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import ConcurrentLeave from "../../../src/components/employers/ConcurrentLeave";
import ConcurrentLeaveModel from "../../../src/models/ConcurrentLeave";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

const CONCURRENT_LEAVE_DATA = {
  is_for_current_employer: true,
  leave_start_date: "2020-03-01",
  leave_end_date: "2020-03-06",
};

describe("ConcurrentLeave", () => {
  const updateFields = jest.fn();
  let getFunctionalInputProps;

  function render(providedProps) {
    const defaultProps = {
      currentConcurrentLeave: new ConcurrentLeaveModel({
        ...CONCURRENT_LEAVE_DATA,
      }),
      getFunctionalInputProps,
      originalConcurrentLeave: new ConcurrentLeaveModel({
        ...CONCURRENT_LEAVE_DATA,
      }),
      updateFields,
    };
    const componentProps = {
      ...defaultProps,
      ...providedProps,
    };
    return shallow(<ConcurrentLeave {...componentProps} />);
  }

  beforeEach(() => {
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState: {},
        updateFields,
      });
    });
  });

  it("renders the component", () => {
    const wrapper = render();
    expect(wrapper).toMatchSnapshot();
  });

  it("displays 'None reported' and the add button if no leave periods are reported", () => {
    const wrapper = render({
      currentConcurrentLeave: null,
      originalConcurrentLeave: null,
    });
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
      originalConcurrentLeave: null,
    });

    expect(wrapper.find("AmendableConcurrentLeave").length).toBe(1);
  });

  it("does not display the add button if there exists an admin-added concurrent leave", () => {
    const wrapper = render({
      originalConcurrentLeave: null,
    });
    expect(wrapper.find("AddButton").exists()).toBe(false);
  });
});
