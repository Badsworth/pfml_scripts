// TODO (PORTAL-1560): Remove this entire file once it's no longer referenced.
import AbsenceCaseStatusTag from "../../components/AbsenceCaseStatusTag";
import ApiResourceCollection from "../../models/ApiResourceCollection";
import { AppLogic } from "../../hooks/useAppLogic";
import Claim from "../../models/Claim";
import Link from "next/link";
import { PageQueryParam } from "./SortDropdown";
import PaginationNavigation from "../../components/PaginationNavigation";
import PaginationSummary from "../../components/PaginationSummary";
import React from "react";
import Table from "../../components/core/Table";
import TooltipIcon from "../../components/core/TooltipIcon";
import { Trans } from "react-i18next";
import User from "../../models/User";
import { WithClaimsProps } from "../../hoc/withClaims";
import formatDateRange from "../../utils/formatDateRange";
import { get } from "lodash";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

interface PaginatedClaimsTableProps extends WithClaimsProps {
  updatePageQuery: (params: PageQueryParam[]) => void;
  /** Pass in the SortDropdown so it can be rendered in the expected inline UI position */
  sort: React.ReactNode;
}

const PaginatedClaimsTable = (props: PaginatedClaimsTableProps) => {
  const { paginationMeta, updatePageQuery, user } = props;
  const { t } = useTranslation();

  const hasOnlyUnverifiedEmployers = user.hasOnlyUnverifiedEmployers;
  const tableColumnVisibility = {
    employee_name: true,
    fineos_absence_id: true,
    employer_dba: user.user_leave_administrators.length > 1,
    employer_fein: true,
    created_at: true,
    status: true,
  };

  /**
   * Columns rendered in the table.
   * Used for rendering header labels and the field(s) in each column. These
   * mostly mirror the name of the fields rendered, but not exactly
   * since some columns might require multiple fields.
   */
  const tableColumnKeys = Object.entries(tableColumnVisibility)
    .filter(([_columnKey, isVisible]) => isVisible)
    .map(([columnKey]) => columnKey);

  /**
   * Event handler for when a next/prev pagination button is clicked
   */
  const handlePaginationNavigationClick = (pageOffset: number | string) => {
    updatePageQuery([
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
                {columnKey === "created_at" && (
                  <TooltipIcon position="bottom">
                    {t("pages.employersDashboard.startDateTooltip")}
                  </TooltipIcon>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {hasOnlyUnverifiedEmployers && (
            <tr data-test="verification-instructions-row">
              <td colSpan={tableColumnKeys.length}>
                <Trans
                  i18nKey="pages.employersDashboard.verificationInstructions"
                  components={{
                    "your-organizations-link": (
                      <a href={routes.employers.organizations} />
                    ),
                  }}
                />
              </td>
            </tr>
          )}
          {!hasOnlyUnverifiedEmployers && (
            <ClaimTableRows
              appLogic={props.appLogic}
              claims={props.claims}
              tableColumnKeys={tableColumnKeys}
              user={user}
            />
          )}
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

interface ClaimTableRowsProps {
  appLogic: AppLogic;
  claims: ApiResourceCollection<Claim>;
  tableColumnKeys: string[];
  user: User;
}

/**
 * Renders the <tr> elements for each claim, or a message indicating
 * no claim data exists
 */
const ClaimTableRows = (props: ClaimTableRowsProps) => {
  const { appLogic, claims, tableColumnKeys, user } = props;
  const { t } = useTranslation();

  if (claims.isEmpty) {
    return (
      <tr>
        <td colSpan={tableColumnKeys.length}>
          {t("pages.employersDashboard.noClaimResults")}
        </td>
      </tr>
    );
  }

  /**
   * Helper for mapping a column key to the value
   * the user should see
   */
  const getValueForColumn = (claim: Claim, columnKey: string) => {
    const claimRoute = appLogic.portalFlow.getNextPageRoute(
      "VIEW_CLAIM",
      {},
      { absence_id: get(claim, "fineos_absence_id") }
    );
    const employerFein = get(claim, "employer.employer_fein");
    const fullName = get(claim, "employee.fullName", "--");
    const isEmployerRegisteredInFineos = user.isEmployerIdRegisteredInFineos(
      get(claim, "employer.employer_id")
    );

    switch (columnKey) {
      case "created_at":
        return formatDateRange(get(claim, columnKey));
      case "fineos_absence_id":
        return isEmployerRegisteredInFineos ? (
          <Link href={claimRoute}>
            <a>{get(claim, columnKey)}</a>
          </Link>
        ) : (
          get(claim, columnKey)
        );
      case "employee_name":
        return isEmployerRegisteredInFineos ? (
          <Link href={claimRoute}>
            <a>{fullName}</a>
          </Link>
        ) : (
          fullName
        );
      case "employer_dba":
        return get(claim, "employer.employer_dba");
      case "employer_fein":
        return employerFein;
      case "status":
        return (
          <AbsenceCaseStatusTag
            status={get(claim, "claim_status")}
            managedRequirements={get(claim, "managed_requirements")}
          />
        );

      default:
        return "";
    }
  };

  const renderClaimItems = () => {
    const claimItemsJSX: JSX.Element[] = [];

    claims.items.forEach((claim) => {
      claimItemsJSX.push(
        <tr key={claim.fineos_absence_id}>
          <th
            scope="row"
            data-label={t("pages.employersDashboard.tableColHeading", {
              context: tableColumnKeys[0],
            })}
            data-test={tableColumnKeys[0]}
          >
            {getValueForColumn(claim, tableColumnKeys[0])}
          </th>
          {tableColumnKeys.slice(1).map((columnKey) => (
            <td
              key={columnKey}
              data-label={t("pages.employersDashboard.tableColHeading", {
                context: columnKey,
              })}
            >
              {getValueForColumn(claim, columnKey)}
            </td>
          ))}
        </tr>
      );
    });

    return claimItemsJSX;
  };

  return <React.Fragment>{renderClaimItems()}</React.Fragment>;
};

export default PaginatedClaimsTable;
