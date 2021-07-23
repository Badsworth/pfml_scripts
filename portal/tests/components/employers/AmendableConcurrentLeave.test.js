import { simulateEvents, testHook } from "../../test-utils";
import AmendableConcurrentLeave from "../../../src/components/employers/AmendableConcurrentLeave";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import ConcurrentLeaveModel from "../../../src/models/ConcurrentLeave";
import React from "react";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

describe("AmendableConcurrentLeave", () => {
  const concurrentLeave = new ConcurrentLeaveModel({
    is_for_current_employer: true,
    leave_start_date: "2020-03-01",
    leave_end_date: "2020-03-06",
  });
  const updateFields = jest.fn();
  let getFunctionalInputProps;

  function render(givenProps = {}) {
    const defaultProps = {
      getFunctionalInputProps,
      isAddedByLeaveAdmin: false,
      originalConcurrentLeave: concurrentLeave,
      updateFields,
    };
    const props = { ...defaultProps, ...givenProps };
    return shallow(<AmendableConcurrentLeave {...props} />);
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

  describe("for claimant-submitted concurrent leaves", () => {
    function clickAmendButton(wrapper) {
      wrapper
        .find("ConcurrentLeaveDetailsRow")
        .dive()
        .find("AmendButton")
        .simulate("click");
    }

    it("renders the component", () => {
      const wrapper = render();
      expect(wrapper).toMatchSnapshot();
    });

    it("renders an AmendmentForm if user clicks on AmendButton", () => {
      const wrapper = render();
      clickAmendButton(wrapper);

      expect(wrapper.find("AmendmentForm").exists()).toEqual(true);
    });

    it("updates start and end dates in the AmendmentForm", () => {
      const wrapper = render();
      clickAmendButton(wrapper);
      const { changeField } = simulateEvents(wrapper);

      changeField("concurrent_leave.leave_start_date", "2020-10-10");
      changeField("concurrent_leave.leave_end_date", "2020-10-20");

      expect(updateFields).toHaveBeenCalledTimes(2);
      expect(updateFields).toHaveBeenNthCalledWith(1, {
        "concurrent_leave.leave_start_date": "2020-10-10",
      });
      expect(updateFields).toHaveBeenNthCalledWith(2, {
        "concurrent_leave.leave_end_date": "2020-10-20",
      });
    });

    it("restores original value on cancel", () => {
      const wrapper = render();
      clickAmendButton(wrapper);
      const { changeField } = simulateEvents(wrapper);

      changeField("concurrent_leave.leave_start_date", "2020-10-10");
      wrapper.find("AmendmentForm").dive().find("Button").simulate("click");

      expect(updateFields).toHaveBeenCalledTimes(2);
      expect(updateFields).toHaveBeenNthCalledWith(2, {
        concurrent_leave: concurrentLeave,
      });
    });
  });

  describe("for admin-added concurrent leaves", () => {
    function renderWithAdminAddedLeave() {
      return render({ isAddedByLeaveAdmin: true });
    }

    it("renders the component", () => {
      const wrapper = renderWithAdminAddedLeave();
      expect(wrapper).toMatchSnapshot();
    });

    it("does not show any ConcurrentLeaveDetailsRow components", () => {
      const wrapper = renderWithAdminAddedLeave();
      expect(wrapper.find("ConcurrentLeaveDetailsRow").exists()).toBe(false);
    });

    it("removes the concurrent leave on cancel", () => {
      const wrapper = renderWithAdminAddedLeave();
      wrapper.find("AmendmentForm").dive().find("Button").simulate("click");
      const { changeField } = simulateEvents(wrapper);

      changeField("concurrent_leave.leave_start_date", "2020-10-10");
      wrapper.find("AmendmentForm").dive().find("Button").simulate("click");

      expect(updateFields).toHaveBeenCalledTimes(3);
      // after "amend" button is clicked.
      expect(updateFields).toHaveBeenNthCalledWith(1, {
        concurrent_leave: null,
      });
      // after field value changed.
      expect(updateFields).toHaveBeenNthCalledWith(2, {
        "concurrent_leave.leave_start_date": "2020-10-10",
      });
      // after "cancel" button clicked..
      expect(updateFields).toHaveBeenNthCalledWith(3, {
        concurrent_leave: null,
      });
    });
  });
});
