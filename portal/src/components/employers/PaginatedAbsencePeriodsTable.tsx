import { AbsencePeriod } from "../../models/AbsencePeriod";
import React from "react";
import { StatusTagMap } from "src/pages/applications/status";
import Table from "../core/Table";
import Tag from "../core/Tag";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

interface PaginatedAbsencePeriodsTableProps {
  absencePeriods: AbsencePeriod[];
}

const PaginatedAbsencePeriodsTable = ({
  absencePeriods,
}: PaginatedAbsencePeriodsTableProps) => {
  const { t } = useTranslation();
  const tableHeadings = [
    t("components.employersPaginationAbsencePeriodsTable.dateRangeLabel"),
    t("components.employersPaginationAbsencePeriodsTable.leaveFrequencyLabel"),
    t("components.employersPaginationAbsencePeriodsTable.statusLabel"),
  ];

  return (
    <Table className="width-full" responsive>
      <thead>
        <tr>
          {tableHeadings.map((heading) => (
            <th key={heading} scope="col">
              {heading}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {absencePeriods.map((period, index) => {
          const tagState =
            StatusTagMap[period.request_decision] === "pending"
              ? "warning"
              : StatusTagMap[period.request_decision];
          return (
            <tr key={index}>
              <th scope="row" data-label={tableHeadings[0]}>
                {formatDateRange(
                  period.absence_period_start_date,
                  period.absence_period_end_date
                )}
              </th>
              <td data-label={tableHeadings[1]}>
                {t(
                  "components.employersPaginationAbsencePeriodsTable.claimDurationType",
                  {
                    context: period.period_type,
                  }
                )}
              </td>
              <td data-label={tableHeadings[2]}>
                <Tag
                  state={tagState}
                  label={t(
                    "components.employersPaginationAbsencePeriodsTable.requestDecision",
                    {
                      context: period.request_decision,
                    }
                  )}
                />
              </td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
};

export default PaginatedAbsencePeriodsTable;
