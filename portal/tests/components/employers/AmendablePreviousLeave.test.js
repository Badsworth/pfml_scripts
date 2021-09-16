import PreviousLeave, {
  PreviousLeaveReason,
  PreviousLeaveType,
} from "../../../src/models/PreviousLeave";
import { fireEvent, render, screen } from "@testing-library/react";
import AmendablePreviousLeave from "../../../src/components/employers/AmendablePreviousLeave";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import React from "react";
import userEvent from "@testing-library/user-event";

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
const appErrors = new AppErrorInfoCollection([]);

const renderAmendedLeave = () => {
  return render(
    <table>
      <tbody>
        <AmendablePreviousLeave
          appErrors={appErrors}
          isAddedByLeaveAdmin={false}
          onChange={onChange}
          onRemove={onRemove}
          previousLeave={previousLeave}
          shouldShowV2
        />
      </tbody>
    </table>
  );
};

const renderAddedLeave = () => {
  return render(
    <table>
      <tbody>
        <AmendablePreviousLeave
          appErrors={appErrors}
          isAddedByLeaveAdmin
          onChange={onChange}
          onRemove={onRemove}
          previousLeave={previousLeave}
          shouldShowV2
        />
      </tbody>
    </table>
  );
};

describe("AmendablePreviousLeave", () => {
  describe("for amended leaves", () => {
    it("renders the component with a table row for existing data", () => {
      const { container } = renderAmendedLeave();
      expect(container.firstChild).toMatchSnapshot();
    });

    it("renders formatted date range for previously existing leave", () => {
      renderAmendedLeave();
      expect(screen.getByText("3/1/2020 to 3/6/2020")).toBeInTheDocument();
    });

    it("renders leave type for existing previous leave", () => {
      renderAmendedLeave();
      expect(
        screen.getByText(
          "Caring for a family member who served in the armed forces"
        )
      ).toBeInTheDocument();
    });

    it("enables updates to start and end dates in the amendment form", () => {
      renderAmendedLeave();
      const amendButton = screen.getByRole("button", { name: "Amend" });
      userEvent.click(amendButton);

      const [startMonthInput, endMonthInput] = screen.getAllByRole("textbox", {
        name: "Month",
      });
      const [startDayInput, endDayInput] = screen.getAllByRole("textbox", {
        name: "Day",
      });
      const [startYearInput, endYearInput] = screen.getAllByRole("textbox", {
        name: "Year",
      });
      expect(startYearInput).toHaveValue("2020");
      expect(startMonthInput).toHaveValue("03");
      expect(startDayInput).toHaveValue("01");
      expect(endMonthInput).toHaveValue("03");
      expect(endDayInput).toHaveValue("06");
      expect(endYearInput).toHaveValue("2020");
      expect(onChange).toHaveBeenCalledTimes(0);

      fireEvent.change(startMonthInput, { target: { value: "05" } });
      expect(onChange).toHaveBeenCalledWith(
        { leave_start_date: "2020-05-01", previous_leave_id: 0 },
        "amendedPreviousLeaves"
      );
      fireEvent.change(endMonthInput, { target: { value: "06" } });
      expect(onChange).toHaveBeenLastCalledWith(
        { leave_end_date: "2020-06-06", previous_leave_id: 0 },
        "amendedPreviousLeaves"
      );
      expect(startMonthInput).toHaveValue("05");
      expect(endMonthInput).toHaveValue("06");
    });

    it("formats empty dates as null instead of empty string", () => {
      renderAmendedLeave();
      userEvent.click(screen.getByRole("button", { name: "Amend" }));
      const dayInputs = screen.getAllByRole("textbox", { name: "Day" });
      const monthInputs = screen.getAllByRole("textbox", { name: "Month" });
      const yearInputs = screen.getAllByRole("textbox", { name: "Year" });
      fireEvent.change(dayInputs[0], { target: { value: "" } });
      fireEvent.change(monthInputs[0], { target: { value: "" } });
      fireEvent.change(yearInputs[0], { target: { value: "" } });

      expect(onChange).toHaveBeenLastCalledWith(
        { leave_start_date: null, previous_leave_id: 0 },
        "amendedPreviousLeaves"
      );
    });

    it("restores original value on cancel, and minimizes form", () => {
      renderAmendedLeave();
      userEvent.click(screen.getByRole("button", { name: "Amend" }));
      expect(screen.getByText(/Amend previous leave/)).toBeInTheDocument();
      const [startYearInput, endYearInput] = screen.getAllByRole("textbox", {
        name: "Year",
      });
      fireEvent.change(startYearInput, { target: { value: "2021" } });
      fireEvent.change(endYearInput, { target: { value: "2021" } });
      expect(endYearInput).toHaveAttribute("value", "2021");

      const cancelButton = screen.getByRole("button", {
        name: "Cancel amendment",
      });
      userEvent.click(cancelButton);
      expect(onChange).toHaveBeenLastCalledWith(
        previousLeave,
        "amendedPreviousLeaves"
      );
      expect(screen.getByText("3/1/2020 to 3/6/2020")).toBeInTheDocument();
      expect(
        screen.queryByText(/Amend previous leave/)
      ).not.toBeInTheDocument();
    });

    it("In v2, enables user to same reason for leave or not", () => {
      renderAmendedLeave();
      userEvent.click(screen.getByRole("button", { name: "Amend" }));

      const sameReasonRadio = screen.getByRole("radio", {
        name: "Yes",
      });
      userEvent.click(sameReasonRadio);
      expect(onChange).toHaveBeenCalledWith(
        {
          type: PreviousLeaveType.sameReason,
          previous_leave_id: 0,
        },
        "amendedPreviousLeaves"
      );
    });

    it("In v2, enables user to change leave reason", () => {
      renderAmendedLeave();
      userEvent.click(screen.getByRole("button", { name: "Amend" }));

      const sameReasonRadio = screen.getByRole("radio", {
        name: "Pregnancy Medical leave",
      });
      userEvent.click(sameReasonRadio);
      expect(onChange).toHaveBeenCalledWith(
        {
          leave_reason: PreviousLeaveReason.pregnancy,
          previous_leave_id: 0,
        },
        "amendedPreviousLeaves"
      );
    });
  });

  describe("for added leaves", () => {
    it("calls onRemove on cancel", () => {
      renderAddedLeave();
      const cancelButton = screen.getByRole("button", {
        name: "Cancel addition",
      });
      userEvent.click(cancelButton);
      expect(onRemove).toHaveBeenCalled();
    });

    it("renders component without the table row", () => {
      renderAddedLeave();
      expect(
        screen.queryByRole("button", { name: "Amend" })
      ).not.toBeInTheDocument();
    });
  });
});
