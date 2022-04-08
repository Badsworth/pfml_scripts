import {
  getLatestFollowUpDate,
  getSoonestReviewableManagedRequirement,
} from "../../models/ManagedRequirement";
import { AbsencePeriod } from "../../models/AbsencePeriod";
import AbsencePeriodStatusTag from "../../components/AbsencePeriodStatusTag";
import ApiResourceCollection from "../../models/ApiResourceCollection";
import ButtonLink from "../../components/ButtonLink";
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
import { compact } from "lodash";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDate from "../../utils/formatDate";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

export interface PaginatedClaimsTableProps extends WithClaimsProps {
  claims: ApiResourceCollection<Claim>;
  getNextPageRoute: PortalFlow["getNextPageRoute"];
  hasOnlyUnverifiedEmployers: boolean;
  paginationMeta: PaginationMeta;
  updatePageQuery: (params: PageQueryParam[]) => void;
  showEmployer: boolean;
  /** Pass in the SortDropdown so it can be rendered in the expected inline UI position */
  sort: React.ReactNode;
}

type TableColumnKey =
  | "employee_and_case"
  | "employer"
  | "leave_details"
  | "review_status";

const PaginatedClaimsTable = (props: PaginatedClaimsTableProps) => {
  const { claims, paginationMeta } = props;
  const { t } = useTranslation();

  /**
   * Columns rendered in the table.
   * Used as i18n context for rendering headers, and determining
   * what content to render in each column.
   */
  const visibleTableColumns: TableColumnKey[] = compact([
    "employee_and_case",
    props.showEmployer ? "employer" : undefined,
    "leave_details",
    "review_status",
  ]);

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
            {visibleTableColumns.map((columnKey) => (
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
              <td colSpan={visibleTableColumns.length}>
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
              <td colSpan={visibleTableColumns.length}>
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
                visibleTableColumns={visibleTableColumns}
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
  visibleTableColumns: TableColumnKey[];
}

const ClaimTableRow = (props: ClaimTableRowProps) => {
  const { claim, visibleTableColumns } = props;
  const { t } = useTranslation();
  const getColumnContents = (columnKey: typeof visibleTableColumns[number]) => {
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
        return <ReviewStatusCell href={props.href} claim={claim} />;
    }
  };

  return (
    <tr className="text-top">
      <th
        scope="row"
        data-label={t("pages.employersDashboard.tableColHeading", {
          context: visibleTableColumns[0],
        })}
      >
        {getColumnContents(visibleTableColumns[0])}
      </th>
      {visibleTableColumns.slice(1).map((columnKey) => (
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
  const maxPeriodsShown = 2;
  const additionalPeriods = absence_periods.length - maxPeriodsShown;

  return (
    <React.Fragment>
      {AbsencePeriod.sortNewToOld(absence_periods)
        .slice(0, maxPeriodsShown)
        .map((period, index) => (
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
      {absence_periods.length > maxPeriodsShown && (
        <div className="grid-row grid-gap padding-top-1">
          <div className="desktop:grid-col-auto minw-15"></div>
          <div className="desktop:grid-col-fill">
            <div className="padding-left-1 text-base-dark">
              {t("pages.employersDashboard.numAbsencePeriodsHidden", {
                hiddenCount: additionalPeriods,
              })}
            </div>
          </div>
        </div>
      )}
    </React.Fragment>
  );
};

const ReviewStatusCell = (props: { href: string; claim: Claim }) => {
  const { t } = useTranslation();
  const { claim } = props;
  const managedRequirements = claim.managed_requirements;
  const isReviewable = claim.isReviewable;

  const reviewableManagedRequirement =
    getSoonestReviewableManagedRequirement(managedRequirements);

  if (managedRequirements.length === 0) {
    return <React.Fragment>--</React.Fragment>;
  }

  if (isReviewable) {
    return (
      <React.Fragment>
        <ButtonLink className="margin-bottom-05" href={props.href}>
          {t("pages.employersDashboard.reviewAction")}
        </ButtonLink>
        <br />
        {t("pages.employersDashboard.respondBy", {
          date: formatDate(
            reviewableManagedRequirement?.follow_up_date
          ).short(),
        })}
      </React.Fragment>
    );
  }

  return (
    <React.Fragment>
      {formatDate(getLatestFollowUpDate(managedRequirements)).short()}
    </React.Fragment>
  );
};

export default PaginatedClaimsTable;
