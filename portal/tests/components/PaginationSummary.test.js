import { render, screen } from "@testing-library/react";
import PaginationSummary from "../../src/components/PaginationSummary";
import React from "react";

describe("PaginationSummary", () => {
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
});
