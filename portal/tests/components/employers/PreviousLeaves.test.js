import PreviousLeave, {
  PreviousLeaveReason,
} from "../../../src/models/PreviousLeave";
import PreviousLeaves from "../../../src/components/employers/PreviousLeaves";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

const PREVIOUS_LEAVES = [
  new PreviousLeave({
    is_for_current_employer: true,
    is_for_same_reason_as_leave_reason: false,
    leave_minutes: 2400,
    leave_reason: PreviousLeaveReason.serviceMemberFamily,
    leave_start_date: "2020-03-01",
    leave_end_date: "2020-03-06",
    previous_leave_id: 0,
    worked_per_week_minutes: 1440,
  }),
  new PreviousLeave({
    is_for_current_employer: true,
    is_for_same_reason_as_leave_reason: true,
    leave_minutes: 4800,
    leave_reason: PreviousLeaveReason.bonding,
    leave_start_date: "2020-05-01",
    leave_end_date: "2020-05-10",
    previous_leave_id: 1,
    worked_per_week_minutes: 960,
  }),
];

describe("PreviousLeaves", () => {
  let appLogic;

  function render(providedProps) {
    const defaultProps = {
      addedPreviousLeaves: [],
      appErrors: appLogic.appErrors,
      onAdd: () => {},
      onChange: () => {},
      onRemove: () => {},
      previousLeaves: PREVIOUS_LEAVES,
      shouldShowV2: true,
    };
    const componentProps = {
      ...defaultProps,
      ...providedProps,
    };
    return shallow(<PreviousLeaves {...componentProps} />);
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

  it("displays 'None reported' if no leave periods are reported", () => {
    const wrapper = render({ previousLeaves: [] });

    expect(wrapper.find("AmendablePreviousLeave").exists()).toEqual(false);
    expect(wrapper.find("th").last().text()).toEqual("None reported");
  });

  it('displays a row for each benefit in "previousLeaves"', () => {
    const wrapper = render();

    expect(wrapper.find("AmendablePreviousLeave").length).toBe(2);
  });

  it("displays rows for added leaves", () => {
    const wrapper = render({
      previousLeaves: [],
      addedPreviousLeaves: PREVIOUS_LEAVES,
    });

    expect(wrapper.find("AmendablePreviousLeave").length).toBe(2);
  });

  it("displays rows for claimant-provided and admin-added leaves simultaneously", () => {
    const wrapper = render({
      previousLeaves: [PREVIOUS_LEAVES[0]],
      addedPreviousLeaves: [PREVIOUS_LEAVES[1]],
    });

    expect(wrapper.find("AmendablePreviousLeave").length).toBe(2);
  });

  it("displays the 'Add leave' button", () => {
    const wrapper = render({
      previousLeaves: [],
      addedPreviousLeaves: PREVIOUS_LEAVES,
    });

    expect(wrapper.find("AddButton").exists()).toBe(true);
  });
});
