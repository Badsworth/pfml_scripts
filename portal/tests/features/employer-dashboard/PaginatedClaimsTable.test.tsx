import { render, screen } from "@testing-library/react";
import ApiResourceCollection from "../../../src/models/ApiResourceCollection";
import Claim from "../../../src/models/Claim";
import PaginatedClaimsTable from "src/features/employer-dashboard/PaginatedClaimsTable";
import React from "react";
import User from "../../../src/models/User";
import { createAbsencePeriod } from "tests/test-utils";
import createMockClaim from "../../../lib/mock-helpers/createMockClaim";
import useMockableAppLogic from "../../../lib/mock-helpers/useMockableAppLogic";

/**
 * A lot of tests for this component's functionality are integration tests,
 * in the Dashboard page's test file. These tests are primarily focused on
 * testing how various absence periods are rendered in the table.
 */
const setup = (claims: Claim[] = []) => {
  const paginationMeta = {
    page_offset: 1,
    page_size: 1,
    total_pages: 1,
    total_records: 1,
    order_by: "created_at",
    order_direction: "ascending",
  } as const;

  const props = {
    claims: new ApiResourceCollection<Claim>("fineos_absence_id", claims),
    getNextPageRoute: jest.fn(), // tested in dashboard page tests, ignoring here.
    hasOnlyUnverifiedEmployers: false,
    paginationMeta,
    sort: <div />, // tested in dashboard page tests, ignoring here.
    updatePageQuery: jest.fn(),
    user: new User({}),
  };

  const PaginatedClaimsTableWithAppLogic = () => {
    const appLogic = useMockableAppLogic();
    return <PaginatedClaimsTable appLogic={appLogic} {...props} />;
  };

  const utils = render(<PaginatedClaimsTableWithAppLogic />);
  return { ...utils };
};

describe("PaginatedClaimsTable", () => {
  it("renders absence periods sorted new to old", () => {
    setup([
      createMockClaim({
        absence_periods: [
          createAbsencePeriod({
            absence_period_start_date: "2021-03-01",
          }),
          createAbsencePeriod({
            absence_period_start_date: "2021-01-01",
          }),
          createAbsencePeriod({
            absence_period_start_date: "2021-02-01",
          }),
        ],
      }),
    ]);

    const absencePeriodParents = screen.getAllByTestId("absence-period");

    expect(absencePeriodParents[0]).toHaveTextContent("3/1/2021");
    expect(absencePeriodParents[1]).toHaveTextContent("2/1/2021");
    expect(absencePeriodParents[2]).toHaveTextContent("1/1/2021");
  });

  it.todo("hides employer column when user only has one employer");
  it.todo("renders a Review call to action when a managed requirement is open");
  it.todo(
    "renders the most recent review date when no managed requirement is open"
  );
});
