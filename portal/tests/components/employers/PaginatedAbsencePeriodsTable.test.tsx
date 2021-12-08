import {
  AbsencePeriod,
  AbsencePeriodRequestDecision,
} from "../../../src/models/AbsencePeriod";
import PaginationAbsencePeriodsTable from "../../../src/components/employers/PaginatedAbsencePeriodsTable";
import React from "react";
import { StatusTagMap } from "../../../src/pages/applications/status";
import { createAbsencePeriod } from "tests/test-utils";
import { render } from "@testing-library/react";

const periodTypes: Array<AbsencePeriod["period_type"]> = [
  "Continuous",
  "Intermittent",
  "Reduced Schedule",
];

const absencePeriodsList = (
  Object.keys(StatusTagMap) as AbsencePeriodRequestDecision[]
).map((status, index) =>
  createAbsencePeriod({
    absence_period_end_date: "2021-09-04",
    absence_period_start_date: "2021-04-09",
    request_decision: status,
    period_type: periodTypes[index % 3],
  })
);

describe("PaginatedAbsencePeriodsTable", () => {
  it("renders the component with absence period list", () => {
    const { container } = render(
      <PaginationAbsencePeriodsTable absencePeriods={absencePeriodsList} />
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
