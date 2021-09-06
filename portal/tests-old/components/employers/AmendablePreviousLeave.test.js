import PreviousLeave, {
  PreviousLeaveReason,
  PreviousLeaveType,
} from "../../../src/models/PreviousLeave";
import AmendablePreviousLeave from "../../../src/components/employers/AmendablePreviousLeave";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

describe("AmendablePreviousLeave", () => {
  const previousLeave = new PreviousLeave({
    is_for_current_employer: true,
    leave_minutes: 2400,
    leave_reason: PreviousLeaveReason.serviceMemberFamily,
    leave_start_date: "2020-03-01",
    leave_end_date: "2020-03-06",
    previous_leave_id: 0,
    type: PreviousLeaveType.otherReason,
    worked_per_week_minutes: 1440,
  });
  const onChange = jest.fn();
  const onRemove = jest.fn();

  let appLogic;

  function renderAmendedLeave() {
    return shallow(
      <AmendablePreviousLeave
        appErrors={appLogic.appErrors}
        isAddedByLeaveAdmin={false}
        onChange={onChange}
        onRemove={onRemove}
        previousLeave={previousLeave}
        shouldShowV2
      />
    );
  }

  function renderAddedLeave() {
    return shallow(
      <AmendablePreviousLeave
        appErrors={appLogic.appErrors}
        isAddedByLeaveAdmin
        onChange={onChange}
        onRemove={onRemove}
        previousLeave={previousLeave}
        shouldShowV2
      />
    );
  }

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
  });

  describe("for amended leaves", () => {
    function clickAmendButton(wrapper) {
      wrapper
        .find("LeaveDetailsRow")
        .dive()
        .find("AmendButton")
        .simulate("click");
    }

    it("renders the component with a table row for existing data", () => {
      const wrapper = renderAmendedLeave();
      expect(wrapper.find("LeaveDetailsRow").exists()).toBe(true);
      expect(wrapper).toMatchSnapshot();
    });

    it("updates start and end dates in the AmendmentForm", () => {
      const wrapper = renderAmendedLeave();
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

    it("renders formatted date range for existing previous leave", () => {
      const wrapper = renderAmendedLeave();
      expect(wrapper.find("LeaveDetailsRow").dive().find("th").text()).toEqual(
        "3/1/2020 to 3/6/2020"
      );
    });

    it("renders leave type for existing previous leave", () => {
      const wrapper = renderAmendedLeave();
      expect(
        wrapper.find("LeaveDetailsRow").dive().find("td").at(0).text()
      ).toEqual("Caring for a family member who served in the armed forces");
    });

    it("formats empty dates to null instead of an empty string", () => {
      const wrapper = renderAmendedLeave();

      clickAmendButton(wrapper);
      wrapper
        .find("InputDate")
        .first()
        .simulate("change", { target: { value: "" } });

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ leave_start_date: null }),
        "amendedPreviousLeaves"
      );
    });

    it("restores original value on cancel", () => {
      const wrapper = renderAmendedLeave();
      clickAmendButton(wrapper);

      wrapper
        .find("InputDate")
        .first()
        .simulate("change", { target: { value: "2020-10-10" } });

      expect(wrapper.find("InputDate").first().prop("value")).toEqual(
        "2020-10-10"
      );

      wrapper
        .find("AmendmentForm")
        .dive()
        .find('[data-test="amendment-destroy-button"]')
        .simulate("click");

      clickAmendButton(wrapper);
      expect(wrapper.find("InputDate").first().prop("value")).toEqual(
        "2020-03-01"
      );
    });
  });

  describe("for added leaves", () => {
    it("renders the component without a table row", () => {
      const wrapper = renderAddedLeave();
      expect(wrapper.find("LeaveDetailsRow").exists()).toBe(false);
      expect(wrapper).toMatchSnapshot();
    });

    it("calls 'onRemove' on cancel", () => {
      const wrapper = renderAddedLeave();
      wrapper
        .find("AmendmentForm")
        .dive()
        .find('[data-test="amendment-destroy-button"]')
        .simulate("click");
      expect(onRemove).toHaveBeenCalled();
    });
  });
});
