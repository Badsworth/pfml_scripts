import { render, screen } from "@testing-library/react";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import Claim from "src/models/Claim";
import MockDate from "mockdate";
import PaginatedClaimsTable from "src/features/employer-dashboard/PaginatedClaimsTable";
import React from "react";
import User from "src/models/User";
import { createAbsencePeriod } from "tests/test-utils";
import createMockClaim from "lib/mock-helpers/createMockClaim";
import { createMockManagedRequirement } from "lib/mock-helpers/createMockManagedRequirement";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

const MOCK_CURRENT_ISO_DATE = "2021-05-01";

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
    getNextPageRoute: jest.fn().mockReturnValue("/mocked-router"), // tested in dashboard page tests, ignoring here.
    hasOnlyUnverifiedEmployers: false,
    paginationMeta,
    showEmployer: true, // tested in dashboard page tests, ignoring here.
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
  beforeAll(() => {
    MockDate.set(MOCK_CURRENT_ISO_DATE);
  });

  it("renders at most two absence periods", () => {
    setup([
      createMockClaim({
        absence_periods: [
          createAbsencePeriod(),
          createAbsencePeriod(),
          createAbsencePeriod(),
        ],
      }),
    ]);

    const absencePeriodParents = screen.getAllByTestId("absence-period");

    expect(absencePeriodParents.length).toEqual(2);
  });

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
  });

  it("renders a Review call to action when a managed requirement is open", () => {
    setup([
      createMockClaim({
        absence_periods: [createAbsencePeriod()],
        managed_requirements: [
          createMockManagedRequirement({
            status: "Open",
            follow_up_date: MOCK_CURRENT_ISO_DATE,
          }),
        ],
      }),
    ]);

    expect(
      screen.getByRole("cell", { name: /Review Application/ })
    ).toMatchSnapshot();
  });

  it("renders the most recent review date when no managed requirement is open", () => {
    setup([
      createMockClaim({
        absence_periods: [createAbsencePeriod()],
        managed_requirements: [
          createMockManagedRequirement({
            status: "Complete",
            follow_up_date: MOCK_CURRENT_ISO_DATE,
          }),
          createMockManagedRequirement({
            status: "Complete",
            follow_up_date: "2020-01-01",
          }),
        ],
      }),
    ]);

    const cells = screen.getAllByRole("cell");

    expect(cells[cells.length - 1]).toMatchSnapshot();
  });

  it("renders '--' for review date when no managed requirements exist", () => {
    setup([
      createMockClaim({
        absence_periods: [createAbsencePeriod()],
        managed_requirements: [],
      }),
    ]);

    const cells = screen.getAllByRole("cell");

    expect(cells[cells.length - 1]).toHaveTextContent("--");
  });
});
