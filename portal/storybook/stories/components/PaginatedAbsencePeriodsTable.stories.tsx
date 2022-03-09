import { AbsencePeriodRequestDecision } from "src/models/AbsencePeriod";
import PaginatedAbsencePeriodsTable from "src/features/employer-review/PaginatedAbsencePeriodsTable";
import React from "react";
import { createAbsencePeriod } from "lib/mock-helpers/createAbsencePeriod";

export default {
  title: "Features/Employer review/PaginatedAbsencePeriodsTable",
  component: PaginatedAbsencePeriodsTable,
};

const shortAbsencePeriodsList = Object.values(AbsencePeriodRequestDecision).map(
  (status) => createAbsencePeriod({ request_decision: status })
);

export const Default = () => (
  <PaginatedAbsencePeriodsTable absencePeriods={shortAbsencePeriodsList} />
);

export const WithPagination = () => (
  <PaginatedAbsencePeriodsTable
    absencePeriods={shortAbsencePeriodsList.concat(shortAbsencePeriodsList)}
  />
);
