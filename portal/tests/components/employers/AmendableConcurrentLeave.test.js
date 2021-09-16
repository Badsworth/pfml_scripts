import { fireEvent, render, screen } from "@testing-library/react";
import AmendableConcurrentLeave from "../../../src/components/employers/AmendableConcurrentLeave";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import ConcurrentLeaveModel from "../../../src/models/ConcurrentLeave";
import React from "react";
import userEvent from "@testing-library/user-event";

const concurrentLeave = new ConcurrentLeaveModel({
  is_for_current_employer: true,
  leave_start_date: "2020-03-01",
  leave_end_date: "2020-03-06",
});
const onChange = jest.fn();
const onRemove = jest.fn();
const appErrors = new AppErrorInfoCollection([]);

const renderComponent = (customProps) => {
  const props = {
    appErrors,
    concurrentLeave,
    isAddedByLeaveAdmin: false,
    onChange,
    onRemove,
    ...customProps,
  };

  // Additional table and tbody tags required to render this component outside of ConcurrentLeave
  return render(
    <table>
      <tbody>
        <AmendableConcurrentLeave {...props} />
      </tbody>
    </table>
  );
};

describe("AmendableConcurrentLeave", () => {
  it("renders the component with initial leave details row", () => {
    const { container } = renderComponent();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("employer can click amend, view amendment form, and make edits", () => {
    renderComponent();
    expect(
      screen.queryByText(/Amend accrued paid leave/)
    ).not.toBeInTheDocument();
    userEvent.click(screen.getByRole("button", { name: "Amend" }));

    expect(screen.getByText(/Amend accrued paid leave/)).toBeInTheDocument();
    const [startMonthInput, endMonthInput] = screen.getAllByRole("textbox", {
      name: "Month",
    });
    const [startDayInput, endDayInput] = screen.getAllByRole("textbox", {
      name: "Day",
    });
    const [startYearInput, endYearInput] = screen.getAllByRole("textbox", {
      name: "Year",
    });
    expect(startMonthInput).toHaveValue("03");
    expect(startDayInput).toHaveValue("01");
    expect(endMonthInput).toHaveValue("03");
    expect(endDayInput).toHaveValue("06");
    expect(endYearInput).toHaveValue("2020");
    expect(onChange).toHaveBeenCalledTimes(0);

    expect(startMonthInput).toHaveAttribute("maxLength", "2");
    fireEvent.change(startYearInput, { target: { value: "2021" } });
    expect(onChange).toHaveBeenCalledWith(
      { leave_start_date: "2021-03-01" },
      "amendedConcurrentLeave"
    );
    fireEvent.change(endYearInput, { target: { value: "2021" } });
    expect(onChange).toHaveBeenLastCalledWith(
      { leave_end_date: "2021-03-06" },
      "amendedConcurrentLeave"
    );
    expect(endYearInput).toHaveValue("2021");
  });

  it("formats empty dates as null instead of empty string", () => {
    renderComponent();
    userEvent.click(screen.getByRole("button", { name: "Amend" }));
    const dayInputs = screen.getAllByRole("textbox", { name: "Day" });
    const monthInputs = screen.getAllByRole("textbox", { name: "Month" });
    const yearInputs = screen.getAllByRole("textbox", { name: "Year" });
    fireEvent.change(dayInputs[0], { target: { value: "" } });
    fireEvent.change(monthInputs[0], { target: { value: "" } });
    fireEvent.change(yearInputs[0], { target: { value: "" } });

    expect(onChange).toHaveBeenLastCalledWith(
      { leave_start_date: null },
      "amendedConcurrentLeave"
    );
  });

  it("restores original value on cancel, and minimizes form", () => {
    renderComponent();
    userEvent.click(screen.getByRole("button", { name: "Amend" }));

    const [startYearInput, endYearInput] = screen.getAllByRole("textbox", {
      name: "Year",
    });
    fireEvent.change(startYearInput, { target: { value: "2021" } });
    fireEvent.change(endYearInput, { target: { value: "2021" } });
    expect(endYearInput).toHaveValue("2021");

    const cancelButton = screen.getByRole("button", {
      name: "Cancel amendment",
    });
    userEvent.click(cancelButton);
    expect(onChange).toHaveBeenLastCalledWith(concurrentLeave);
    expect(screen.getByText("3/1/2020 to 3/6/2020")).toBeInTheDocument();
    expect(
      screen.queryByText(/Amend accrued paid leave/)
    ).not.toBeInTheDocument();
  });

  it("renders expected ui for admin added leaves", () => {
    const { container } = renderComponent({ isAddedByLeaveAdmin: true });
    expect(container.firstChild).toMatchSnapshot();
  });

  it("calls onRemove on cancel for admin added leaves", () => {
    renderComponent({ isAddedByLeaveAdmin: true });
    const cancelButton = screen.getByRole("button", {
      name: "Cancel addition",
    });
    userEvent.click(cancelButton);
    expect(onRemove).toHaveBeenCalled();
  });

  it("does not display ConcurrentLeaveDetailsRow for admin added leaves", () => {
    renderComponent({ isAddedByLeaveAdmin: true });
    expect(
      screen.queryByRole("button", { name: "Amend" })
    ).not.toBeInTheDocument();
  });
});
