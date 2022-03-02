import { render, screen } from "@testing-library/react";
import ConcurrentLeave from "../../../src/features/employer-review/ConcurrentLeave";
import ConcurrentLeaveModel from "../../../src/models/ConcurrentLeave";
import React from "react";
import { createMockEmployerClaim } from "../../test-utils";

const CONCURRENT_LEAVE = new ConcurrentLeaveModel({
  is_for_current_employer: true,
  leave_start_date: "2020-03-01",
  leave_end_date: "2020-03-06",
});

const defaultProps = {
  addedConcurrentLeave: null,
  errors: [],
  concurrentLeave: CONCURRENT_LEAVE,
  claim: createMockEmployerClaim("completed"),
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

  it("displays correct conditional text for reduced concurrent leave", () => {
    renderComponent({
      addedConcurrentLeave: CONCURRENT_LEAVE,
      claim: createMockEmployerClaim("reducedScheduleAbsencePeriod"),
      concurrentLeave: null,
    });

    expect(
      screen.getByText(
        /your employee won’t receive pfml payments for the first 7 calendar days of their pfml leave from 5\/1\/2022 to 5\/7\/2022\./i
      )
    ).toBeInTheDocument();
  });

  it("displays correct conditional text for continuous concurrent leave", () => {
    renderComponent({
      addedConcurrentLeave: CONCURRENT_LEAVE,
      claim: createMockEmployerClaim("continuousAbsencePeriod"),
      concurrentLeave: null,
    });

    expect(
      screen.getByText(
        /your employee won’t receive pfml payments for the first 7 calendar days of their pfml leave from 1\/1\/2022 to 1\/7\/2022\./i
      )
    ).toBeInTheDocument();
  });

  it("displays correct conditional text for intermittent concurrent leave", () => {
    renderComponent({
      addedConcurrentLeave: CONCURRENT_LEAVE,
      claim: createMockEmployerClaim("intermittent"),
      concurrentLeave: null,
    });
    expect(
      screen.getByText(
        /your employee won’t receive pfml payments for the first 7 calendar days from the date of their first instance of leave\./i
      )
    ).toBeInTheDocument();
  });
});
