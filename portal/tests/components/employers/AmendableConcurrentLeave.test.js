import AmendableConcurrentLeave from "../../../src/components/employers/AmendableConcurrentLeave";
import ConcurrentLeaveModel from "../../../src/models/ConcurrentLeave";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

describe("AmendableConcurrentLeave", () => {
  const concurrentLeave = new ConcurrentLeaveModel({
    is_for_current_employer: true,
    leave_start_date: "2020-03-01",
    leave_end_date: "2020-03-06",
  });
  const onChange = jest.fn();
  const onRemove = jest.fn();

  let appLogic, wrapper;

  describe("for claimant-submitted concurrent leaves", () => {
    function clickAmendButton(wrapper) {
      wrapper
        .find("ConcurrentLeaveDetailsRow")
        .dive()
        .find("AmendButton")
        .simulate("click");
    }

    beforeEach(() => {
      testHook(() => {
        appLogic = useAppLogic();
      });

      wrapper = shallow(
        <AmendableConcurrentLeave
          appErrors={appLogic.appErrors}
          concurrentLeave={concurrentLeave}
          isAddedByLeaveAdmin={false}
          onChange={onChange}
          onRemove={onRemove}
        />
      );
    });

    it("renders the component", () => {
      expect(wrapper).toMatchSnapshot();
    });

    it("renders an AmendmentForm if user clicks on AmendButton", () => {
      clickAmendButton(wrapper);

      expect(wrapper.find("AmendmentForm").exists()).toEqual(true);
    });

    it("updates start and end dates in the AmendmentForm", () => {
      clickAmendButton(wrapper);
      wrapper
        .find("InputDate")
        .first()
        .simulate("change", { target: { value: "2020-10-10" } });
      wrapper
        .find("InputDate")
        .last()
        .simulate("change", { target: { value: "2020-10-20" } });

      expect(onChange).toHaveBeenCalledTimes(2);
      expect(wrapper.find("InputDate").first().prop("value")).toEqual(
        "2020-10-10"
      );
      expect(wrapper.find("InputDate").last().prop("value")).toEqual(
        "2020-10-20"
      );
    });

    it("formats empty dates to null instead of an empty string", () => {
      clickAmendButton(wrapper);
      wrapper
        .find("InputDate")
        .first()
        .simulate("change", { target: { value: "" } });

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ leave_start_date: null }),
        "amendedConcurrentLeave"
      );
    });

    it("restores original value on cancel", () => {
      clickAmendButton(wrapper);
      wrapper
        .find("InputDate")
        .first()
        .simulate("change", { target: { value: "2020-10-10" } });

      expect(wrapper.find("InputDate").first().prop("value")).toEqual(
        "2020-10-10"
      );

      wrapper.find("AmendmentForm").dive().find("Button").simulate("click");

      clickAmendButton(wrapper);
      expect(wrapper.find("InputDate").first().prop("value")).toEqual(
        "2020-03-01"
      );
    });
  });

  describe("for admin-added concurrent leaves", () => {
    beforeEach(() => {
      testHook(() => {
        appLogic = useAppLogic();
      });

      wrapper = shallow(
        <AmendableConcurrentLeave
          appErrors={appLogic.appErrors}
          concurrentLeave={concurrentLeave}
          isAddedByLeaveAdmin
          onChange={onChange}
          onRemove={onRemove}
        />
      );
    });

    it("renders the component", () => {
      expect(wrapper).toMatchSnapshot();
    });

    it("does not show any ConcurrentLeaveDetailsRow components", () => {
      expect(wrapper.find("ConcurrentLeaveDetailsRow").exists()).toBe(false);
    });

    it("calls 'onRemove' value on cancel", () => {
      wrapper.find("AmendmentForm").dive().find("Button").simulate("click");
      expect(onRemove).toHaveBeenCalled();
    });
  });
});
