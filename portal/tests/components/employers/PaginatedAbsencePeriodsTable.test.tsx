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
