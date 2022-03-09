import React, { useRef } from "react";
import { AbsencePeriod } from "../../models/AbsencePeriod";
import AbsencePeriodStatusTag from "../../components/AbsencePeriodStatusTag";
import PaginationNavigation from "../../components/PaginationNavigation";
import PaginationSummary from "../../components/PaginationSummary";
import Table from "../../components/core/Table";
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
  const pageSize = 10;
  const totalRecords = absencePeriods.length;
  const totalPages = Math.ceil(totalRecords / pageSize);
  const showPagination = totalPages > 1;

  // Map absence periods array into the corresponding page offset,
  // allow us to retrieve absence periods by page offset
  // e.g. {1: absencePeriods[0-9], 2: absencePeriods[10-19]}
  const absencePeriodsWithPageOffsetMap = new Map<number, AbsencePeriod[]>();
  const pages = Array.from(Array(totalPages), (_, index) => index + 1);
  pages.forEach((page) =>
    absencePeriodsWithPageOffsetMap.set(
      page,
      absencePeriods.slice(
        (page - 1) * pageSize,
        (page - 1) * pageSize + pageSize
      )
    )
  );

  const [currentPage, setCurrentPage] = React.useState<number>(1);
  const tableRef = useRef<null | HTMLTableSectionElement>(null);

  const handlePaginationNavigationClick = (pageOffset: number) => {
    const topOfTableCoordinate = Number(
      tableRef.current?.getBoundingClientRect().top
    );
    // only scroll into view if table is not in view
    if (topOfTableCoordinate < 0) tableRef.current?.scrollIntoView();
    setCurrentPage(pageOffset);
  };

  return (
    <React.Fragment>
      {showPagination && (
        <PaginationSummary
          pageOffset={currentPage}
          pageSize={pageSize}
          totalRecords={totalRecords}
        />
      )}
      <Table className="width-full" responsive>
        <thead ref={tableRef}>
          <tr>
            {tableHeadings.map((heading) => (
              <th key={heading} scope="col">
                {heading}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {absencePeriodsWithPageOffsetMap
            .get(currentPage)
            ?.map((period, index) => {
              return (
                <tr
                  key={`${currentPage}-${index}`}
                  data-testid={`${currentPage}-${index}`}
                >
                  <th
                    className="tablet:width-card-lg"
                    scope="row"
                    data-label={tableHeadings[0]}
                  >
                    {formatDateRange(
                      period.absence_period_start_date,
                      period.absence_period_end_date
                    )}
                  </th>
                  <td
                    className="tablet:width-card-lg"
                    data-label={tableHeadings[1]}
                  >
                    {t(
                      "components.employersPaginationAbsencePeriodsTable.claimDurationType",
                      {
                        context: period.period_type,
                      }
                    )}
                  </td>
                  <td data-label={tableHeadings[2]}>
                    <AbsencePeriodStatusTag
                      request_decision={period.request_decision}
                    />
                  </td>
                </tr>
              );
            })}
        </tbody>
      </Table>
      {showPagination && (
        <PaginationNavigation
          pageOffset={currentPage}
          totalPages={totalPages}
          onClick={handlePaginationNavigationClick}
        />
      )}
    </React.Fragment>
  );
};

export default PaginatedAbsencePeriodsTable;
