import { AbsencePeriodRequestDecision } from "src/models/AbsencePeriod";
import PaginatedAbsencePeriodsTable from "src/components/employers/PaginatedAbsencePeriodsTable";
import React from "react";
import { createAbsencePeriod } from "lib/mock-helpers/createAbsencePeriod";

export default {
  title: "Components/PaginatedAbsencePeriodsTable",
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
