import PaginatedAbsencePeriodsTable from "src/components/employers/PaginatedAbsencePeriodsTable";
import React from "react";
import { StatusTagMap } from "src/pages/applications/status";
import { createAbsencePeriod } from "lib/mock-helpers/createAbsencePeriod";

export default {
  title: "Components/PaginatedAbsencePeriodsTable",
  component: PaginatedAbsencePeriodsTable,
};

const shortAbsencePeriodsList = (
  Object.keys(StatusTagMap) as Array<keyof typeof StatusTagMap>
).map((status) => createAbsencePeriod({ request_decision: status }));

export const Default = () => (
  <PaginatedAbsencePeriodsTable absencePeriods={shortAbsencePeriodsList} />
);

export const WithPagination = () => (
  <PaginatedAbsencePeriodsTable
    absencePeriods={shortAbsencePeriodsList.concat(shortAbsencePeriodsList)}
  />
);
