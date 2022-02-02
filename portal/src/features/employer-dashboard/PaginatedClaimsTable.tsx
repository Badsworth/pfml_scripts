import { AbsencePeriod } from "../../models/AbsencePeriod";
import AbsencePeriodStatusTag from "../../components/AbsencePeriodStatusTag";
import ApiResourceCollection from "../../models/ApiResourceCollection";
import Claim from "../../models/Claim";
import LeaveReason from "../../models/LeaveReason";
import Link from "next/link";
import { PageQueryParam } from "./SortDropdown";
import PaginationMeta from "../../models/PaginationMeta";
import PaginationNavigation from "../../components/PaginationNavigation";
import PaginationSummary from "../../components/PaginationSummary";
import { PortalFlow } from "../../hooks/usePortalFlow";
import React from "react";
import Table from "../../components/core/Table";
import { Trans } from "react-i18next";
import { WithClaimsProps } from "../../hoc/withClaims";
import classNames from "classnames";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

/**
 * Columns rendered in the table.
 * Used as i18n context for rendering headers, and determining
 * what content to render in each column.
 */
const tableColumnKeys = [
  "employee_and_case",
  "employer",
  "leave_details",
  "review_status",
] as const;

export interface PaginatedClaimsTableProps extends WithClaimsProps {
  claims: ApiResourceCollection<Claim>;
  getNextPageRoute: PortalFlow["getNextPageRoute"];
  hasOnlyUnverifiedEmployers: boolean;
  paginationMeta: PaginationMeta;
  updatePageQuery: (params: PageQueryParam[]) => void;
  /** Pass in the SortDropdown so it can be rendered in the expected inline UI position */
  sort: React.ReactNode;
}

const PaginatedClaimsTable = (props: PaginatedClaimsTableProps) => {
  const { claims, paginationMeta } = props;
  const { t } = useTranslation();

  /** Helper for determining what to display in our table body. Keeps conditions simpler in our render section */
  const getTableBodyState = () => {
    if (props.hasOnlyUnverifiedEmployers) return "no_verifications";
    return claims.isEmpty ? "empty" : "show_claims";
  };
  const tableBodyState = getTableBodyState();

  const handlePaginationNavigationClick = (pageOffset: number) => {
    props.updatePageQuery([
      {
        name: "page_offset",
        value: pageOffset,
      },
    ]);
  };

  return (
    <React.Fragment>
      <div className="margin-y-2 grid-row grid-gap flex-align-center">
        <div className="grid-col grid-col-12 margin-bottom-2 mobile-lg:grid-col-fill mobile-lg:margin-bottom-0">
          <PaginationSummary
            pageOffset={paginationMeta.page_offset}
            pageSize={paginationMeta.page_size}
            totalRecords={paginationMeta.total_records}
          />
        </div>
        <div className="grid-col grid-col-auto">{props.sort}</div>
      </div>
      <Table className="width-full" responsive scrollable>
        <thead>
          <tr>
            {tableColumnKeys.map((columnKey) => (
              <th key={columnKey} scope="col">
                {t("pages.employersDashboard.tableColHeading", {
                  context: columnKey,
                })}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tableBodyState === "no_verifications" && (
            <tr data-test="verification-instructions-row">
              <td colSpan={tableColumnKeys.length}>
                <Trans
                  i18nKey="pages.employersDashboard.verificationInstructions"
                  components={{
                    "your-organizations-link": (
                      <a href={props.getNextPageRoute("VERIFY_ORG")} />
                    ),
                  }}
                />
              </td>
            </tr>
          )}
          {tableBodyState === "empty" && (
            <tr>
              <td colSpan={tableColumnKeys.length}>
                {t("pages.employersDashboard.noClaimResults")}
              </td>
            </tr>
          )}
          {tableBodyState === "show_claims" &&
            claims.items.map((claim) => (
              <ClaimTableRow
                key={claim.fineos_absence_id}
                claim={claim}
                href={props.getNextPageRoute(
                  "VIEW_CLAIM",
                  {},
                  { absence_id: claim.fineos_absence_id }
                )}
              />
            ))}
        </tbody>
      </Table>
      {paginationMeta.total_pages > 1 && (
        <PaginationNavigation
          pageOffset={paginationMeta.page_offset}
          totalPages={paginationMeta.total_pages}
          onClick={handlePaginationNavigationClick}
        />
      )}
    </React.Fragment>
  );
};

interface ClaimTableRowProps {
  claim: Claim;
  href: string;
}

const ClaimTableRow = (props: ClaimTableRowProps) => {
  const { claim } = props;
  const { t } = useTranslation();

  const getColumnContents = (columnKey: typeof tableColumnKeys[number]) => {
    switch (columnKey) {
      case "employee_and_case":
        return (
          <Link href={props.href}>
            <a>
              {claim.employee?.fullName || "--"}
              <div className="font-body-2xs text-normal">
                {claim.fineos_absence_id}
              </div>
            </a>
          </Link>
        );
      case "employer":
        /* TODO (PORTAL-1615): Hide this column when there's only one org */
        return (
          <div className="text-wrap">
            {claim.employer.employer_dba}
            <div className="font-body-2xs text-base-dark">
              {claim.employer.employer_fein}
            </div>
          </div>
        );
      case "leave_details":
        return <LeaveDetailsCell absence_periods={claim.absence_periods} />;
      case "review_status":
        return <React.Fragment>{/* TODO (PORTAL-1615) */}</React.Fragment>;
    }
  };

  return (
    <tr className="text-top">
      <th
        scope="row"
        data-label={t("pages.employersDashboard.tableColHeading", {
          context: tableColumnKeys[0],
        })}
      >
        {getColumnContents(tableColumnKeys[0])}
      </th>
      {tableColumnKeys.slice(1).map((columnKey) => (
        <td
          key={columnKey}
          data-label={t("pages.employersDashboard.tableColHeading", {
            context: columnKey,
          })}
        >
          {getColumnContents(columnKey)}
        </td>
      ))}
    </tr>
  );
};

const LeaveDetailsCell = (props: {
  absence_periods: Claim["absence_periods"];
}) => {
  const { absence_periods } = props;
  const { t } = useTranslation();

  return (
    <React.Fragment>
      {AbsencePeriod.sortNewToOld(absence_periods).map((period, index) => (
        <div
          key={index}
          className={classNames(
            "grid-row grid-gap-1",
            // Put space between the cell's heading when stacked
            "margin-top-1 mobile-lg:margin-top-0",
            {
              // Put space between the absence periods
              "padding-top-2": index > 0,
            }
          )}
          data-testid="absence-period"
        >
          <div className="desktop:grid-col-auto">
            {/* 2px top margin to vertically align text when side-by-side */}
            <AbsencePeriodStatusTag
              className="minw-15 margin-top-2px margin-bottom-05"
              request_decision={period.request_decision}
            />
          </div>
          <div className="desktop:grid-col-fill text-wrap">
            <div className="text-medium">
              {t("pages.employersDashboard.absencePeriodReason", {
                context: findKeyByValue(LeaveReason, period.reason),
              })}
            </div>

            {formatDateRange(
              period.absence_period_start_date,
              period.absence_period_end_date
            )}

            <div className="font-body-2xs">
              {t("pages.employersDashboard.absencePeriodType", {
                context: period.period_type,
              })}
            </div>
          </div>
        </div>
      ))}
    </React.Fragment>
  );
};

export default PaginatedClaimsTable;
