import {
  AbsencePeriod,
  AbsencePeriodRequestDecision,
} from "src/models/AbsencePeriod";
import { render, screen } from "@testing-library/react";
import PaginationAbsencePeriodsTable from "src/features/employer-review/PaginatedAbsencePeriodsTable";
import React from "react";
import { createAbsencePeriod } from "tests/test-utils";
import userEvent from "@testing-library/user-event";

const periodTypes: Array<AbsencePeriod["period_type"]> = [
  "Continuous",
  "Intermittent",
  "Reduced Schedule",
];

const absencePeriodsList = Object.values(AbsencePeriodRequestDecision).map(
  (status, index) =>
    createAbsencePeriod({
      absence_period_end_date: "2021-09-04",
      absence_period_start_date: "2021-04-09",
      request_decision: status,
      period_type: periodTypes[index % 3],
    })
);

const longAbsencePeriodsList = absencePeriodsList.concat(absencePeriodsList);

describe("PaginatedAbsencePeriodsTable", () => {
  it("renders the component", () => {
    const { container } = render(
      <PaginationAbsencePeriodsTable absencePeriods={absencePeriodsList} />
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it("renders pagination parts when absence period list is longer than 10", () => {
    render(
      <PaginationAbsencePeriodsTable absencePeriods={absencePeriodsList} />
    );

    expect(screen.queryByText(/Viewing 1 to 10 of/)).not.toBeInTheDocument();
    expect(
      screen.queryByRole("navigation", { name: "Pagination Navigation" })
    ).not.toBeInTheDocument();

    render(
      <PaginationAbsencePeriodsTable absencePeriods={longAbsencePeriodsList} />
    );

    expect(screen.getByText(/Viewing 1 to 10 of/)).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Pagination Navigation" })
    ).toBeInTheDocument();
  });

  it("changes table contents when clicking the nav button", () => {
    render(
      <PaginationAbsencePeriodsTable absencePeriods={longAbsencePeriodsList} />
    );

    expect(screen.getAllByTestId(/1-/).length).toBe(10);

    userEvent.click(screen.getByRole("button", { name: "Go to Next page" }));
    expect(screen.queryAllByTestId(/1-/).length).toBe(0);
    expect(screen.getAllByTestId(/2-/).length).toBe(
      longAbsencePeriodsList.length - 10
    );
  });
});
