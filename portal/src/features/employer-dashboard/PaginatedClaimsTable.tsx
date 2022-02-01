import ApiResourceCollection from "../../models/ApiResourceCollection";
import Claim from "../../models/Claim";
import { PageQueryParam } from "./SortDropdown";
import PaginationMeta from "../../models/PaginationMeta";
import PaginationNavigation from "../../components/PaginationNavigation";
import PaginationSummary from "../../components/PaginationSummary";
import { PortalFlow } from "../../hooks/usePortalFlow";
import React from "react";
import Table from "../../components/core/Table";
import { Trans } from "react-i18next";
import { WithClaimsProps } from "../../hoc/withClaims";
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
              <ClaimTableRow key={claim.fineos_absence_id} claim={claim} />
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
}

const ClaimTableRow = (props: ClaimTableRowProps) => {
  const { claim } = props;
  const { t } = useTranslation();
  const getColumnContents = (columnKey: typeof tableColumnKeys[number]) => {
    switch (columnKey) {
      case "employee_and_case":
        return (
          <React.Fragment>
            {claim.employee?.fullName || "--"}
            {claim.fineos_absence_id}
          </React.Fragment>
        );
      default:
        break;
    }
  };

  return (
    <tr>
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

export default PaginatedClaimsTable;
