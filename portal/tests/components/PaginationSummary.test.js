import { render, screen } from "@testing-library/react";
import PaginationSummary from "../../src/components/PaginationSummary";
import React from "react";

describe("PaginationSummary", () => {
  it("announces changes to assistive devices like screen readers", () => {
    render(
      <PaginationSummary pageOffset={2} pageSize={25} totalRecords={7500} />
    );

    expect(screen.getByText(/Viewing/)).toHaveAttribute("aria-live", "polite");
  });

  it("displays numbers of first and last records for selected page and total number of records", () => {
    render(
      <PaginationSummary pageOffset={2} pageSize={25} totalRecords={7500} />
    );
    expect(
      screen.getByText("Viewing 26 to 50 of 7,500 results")
    ).toBeInTheDocument();
  });

  it("displays only up to the total number of records, even if it is less than the page size", () => {
    render(
      <PaginationSummary pageOffset={1} pageSize={25} totalRecords={20} />
    );
    expect(
      screen.getByText("Viewing 1 to 20 of 20 results")
    ).toBeInTheDocument();
  });

  it("displays unique message if there are no results", () => {
    render(<PaginationSummary pageOffset={1} pageSize={25} totalRecords={0} />);

    expect(screen.getByText("0 results")).toBeInTheDocument();
  });
});
