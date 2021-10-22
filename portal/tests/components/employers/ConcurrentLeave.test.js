import { render, screen } from "@testing-library/react";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import ConcurrentLeave from "../../../src/components/employers/ConcurrentLeave";
import ConcurrentLeaveModel from "../../../src/models/ConcurrentLeave";
import React from "react";

const CONCURRENT_LEAVE = new ConcurrentLeaveModel({
  is_for_current_employer: true,
  leave_start_date: "2020-03-01",
  leave_end_date: "2020-03-06",
});

const defaultProps = {
  addedConcurrentLeave: null,
  appErrors: new AppErrorInfoCollection(),
  concurrentLeave: CONCURRENT_LEAVE,
  onAdd: jest.fn(),
  onChange: jest.fn(),
  onRemove: jest.fn(),
};

const renderComponent = (props = {}) => {
  return render(<ConcurrentLeave {...defaultProps} {...props} />);
};

describe("ConcurrentLeave", () => {
  it("renders the component", () => {
    const { container } = renderComponent();
    expect(container).toMatchSnapshot();
  });

  it("displays 'None reported' and the add button if no leave periods are reported", () => {
    renderComponent({ concurrentLeave: null });
    expect(
      screen.getByRole("row", { name: "None reported" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Add an accrued paid leave" })
    ).toBeInTheDocument();
  });

  it("displays a row for claimant-submitted concurrent leave", () => {
    renderComponent();
    expect(
      screen.getByRole("rowheader", { name: "3/1/2020 to 3/6/2020" })
    ).toBeInTheDocument();
  });

  it("does not display the add button if there exists a claimant-submitted concurrent leave", () => {
    renderComponent();
    expect(
      screen.queryByRole("button", { name: "Add an accrued paid leave" })
    ).not.toBeInTheDocument();
  });

  it("displays a row for admin-added concurrent leave", () => {
    renderComponent({
      addedConcurrentLeave: CONCURRENT_LEAVE,
      concurrentLeave: null,
    });

    expect(
      screen.getByRole("group", { name: "When did the leave begin?" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("group", { name: "When did the leave end?" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Cancel addition" })
    ).toBeInTheDocument();
  });

  it("does not display the add button if there exists an admin-added concurrent leave", () => {
    renderComponent({
      addedConcurrentLeave: CONCURRENT_LEAVE,
      concurrentLeave: null,
    });
    expect(
      screen.queryByRole("button", { name: "Add an accrued paid leave" })
    ).not.toBeInTheDocument();
  });
});
