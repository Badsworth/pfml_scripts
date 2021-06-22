import AbsenceCaseStatusTag from "../../components/AbsenceCaseStatusTag";
import Alert from "../../components/Alert";
import ClaimCollection from "../../models/ClaimCollection";
import Details from "../../components/Details";
import Dropdown from "../../components/Dropdown";
import EmployerNavigationTabs from "../../components/employers/EmployerNavigationTabs";
import PaginationMeta from "../../models/PaginationMeta";
import PaginationNavigation from "../../components/PaginationNavigation";
import PaginationSummary from "../../components/PaginationSummary";
import PropTypes from "prop-types";
import React from "react";
import Table from "../../components/Table";
import Title from "../../components/Title";
import TooltipIcon from "../../components/TooltipIcon";
import { Trans } from "react-i18next";
import User from "../../models/User";
import formatDateRange from "../../utils/formatDateRange";
import { get } from "lodash";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaims from "../../hoc/withClaims";

export const Dashboard = (props) => {
  const { appLogic, paginationMeta, user } = props;
  const { t } = useTranslation();

  const hasOnlyUnverifiedEmployers = user.hasOnlyUnverifiedEmployers;
  const hasVerifiableEmployer = user.hasVerifiableEmployer;

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
   * @type {string[]}
   */
  const tableColumnKeys = Object.entries(tableColumnVisibility)
    .filter(([columnKey, isVisible]) => isVisible)
    .map(([columnKey, isVisible]) => columnKey);

  /**
   * Update the page's query string, to load a different page number,
   * or change the filter/sort of the loaded claims. The name/value
   * are merged with the existing query string.
   * @param {Array<{ name: string, value: number|string }>} paramsToUpdate
   */
  const updateClaimsRequestParams = (paramsToUpdate) => {
    const params = new URLSearchParams(window.location.search);

    paramsToUpdate.forEach(({ name, value }) => {
      if (!value) {
        params.delete(name);
      } else {
        params.set(name, value);
      }
    });

    const paramsObj = {};
    for (const [paramKey, paramValue] of params.entries()) {
      paramsObj[paramKey] = paramValue;
    }

    // Our withClaims component watches the query string and
    // will trigger an API request when it changes.
    appLogic.portalFlow.goTo(appLogic.portalFlow.pathname, paramsObj);
  };

  /**
   * Event handler for when a next/prev pagination button is clicked
   * @param {number|string} pageOffset - Page number to load
   */
  const handlePaginationNavigationClick = (pageOffset) => {
    updateClaimsRequestParams([
      {
        name: "page_offset",
        value: pageOffset,
      },
    ]);
  };

  return (
    <React.Fragment>
      <EmployerNavigationTabs activePath={appLogic.portalFlow.pathname} />
      <Title>{t("pages.employersDashboard.title")}</Title>

      <div className="measure-6">
        {hasVerifiableEmployer && (
          <Alert
            state="warning"
            heading={t("pages.employersDashboard.verificationTitle")}
          >
            <p>
              <Trans
                i18nKey="pages.employersDashboard.verificationBody"
                components={{
                  "your-organizations-link": (
                    <a href={routes.employers.organizations} />
                  ),
                }}
              />
            </p>
          </Alert>
        )}

        <DashboardInfoAlert user={user} />
      </div>

      <section className="margin-bottom-4">
        <p className="margin-y-2">
          {t("pages.employersDashboard.instructions")}
        </p>
        <Details label={t("pages.employersDashboard.statusDescriptionsLabel")}>
          <ul className="usa-list">
            <li>
              <Trans i18nKey="pages.employersDashboard.statusDescription_none" />
            </li>
            <li>
              <Trans i18nKey="pages.employersDashboard.statusDescription_approved" />
            </li>
            <li>
              <Trans i18nKey="pages.employersDashboard.statusDescription_closed" />
            </li>
            <li>
              <Trans i18nKey="pages.employersDashboard.statusDescription_denied" />
            </li>
          </ul>
        </Details>
      </section>

      {isFeatureEnabled("employerShowDashboardEmployerFilter") && (
        <Filters
          activeFilters={props.activeFilters}
          updateClaimsRequestParams={updateClaimsRequestParams}
          user={user}
        />
      )}

      {paginationMeta.total_records > 0 && (
        <PaginationSummary
          pageOffset={paginationMeta.page_offset}
          pageSize={paginationMeta.page_size}
          totalRecords={paginationMeta.total_records}
        />
      )}
      <Table className="width-full tablet:width-auto" responsive scrollable>
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

Dashboard.propTypes = {
  activeFilters: PropTypes.shape({
    employer_id: PropTypes.string,
  }).isRequired,
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
      goTo: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
  claims: PropTypes.instanceOf(ClaimCollection),
  paginationMeta: PropTypes.instanceOf(PaginationMeta),
  user: PropTypes.instanceOf(User).isRequired,
};

/**
 * Renders the <tr> elements for each claim, or a message indicating
 * no claim data exists
 */
const ClaimTableRows = (props) => {
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
   * @param {EmployerClaim} claim
   * @param {string} columnKey
   * @returns {string|React.ReactNode}
   */
  const getValueForColumn = (claim, columnKey) => {
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
          <a href={claimRoute}>{get(claim, columnKey)}</a>
        ) : (
          get(claim, columnKey)
        );
      case "employee_name":
        return isEmployerRegisteredInFineos ? (
          <a href={claimRoute}>{fullName}</a>
        ) : (
          fullName
        );
      case "employer_dba":
        return get(claim, "employer.employer_dba");
      case "employer_fein":
        return employerFein;
      case "status":
        return <AbsenceCaseStatusTag status={get(claim, "claim_status")} />;
      default:
        return "";
    }
  };

  return claims.items.map((claim) => (
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
  ));
};

ClaimTableRows.propTypes = {
  appLogic: Dashboard.propTypes.appLogic,
  claims: Dashboard.propTypes.claims,
  tableColumnKeys: PropTypes.arrayOf(PropTypes.string).isRequired,
  user: PropTypes.instanceOf(User).isRequired,
};

const DashboardInfoAlert = (props) => {
  const { user } = props;
  const { t } = useTranslation();

  const getCommaDelimitedEmployerEINs = () => {
    const employers = user.verifiedEmployersNotRegisteredInFineos;
    return employers.map((employer) => employer.employer_fein).join(", ");
  };

  // Leave admins not registered in Fineos won't be able to access associated claim data from Fineos.
  // We use this flag to communicate this to the user.
  if (user.hasVerifiedEmployerNotRegisteredInFineos) {
    return (
      <Alert
        state="info"
        heading={t("pages.employersDashboard.unavailableClaimsTitle", {
          employers: getCommaDelimitedEmployerEINs(),
        })}
      >
        <p>
          <Trans
            i18nKey="pages.employersDashboard.unavailableClaimsBody"
            components={{
              "learn-more-link": (
                <a
                  href={routes.external.massgov.employerAccount}
                  target="_blank"
                  rel="noopener"
                />
              ),
            }}
          />
        </p>
      </Alert>
    );
  }

  return (
    <Alert state="info" heading={t("pages.employersDashboard.betaHeader")}>
      <p>
        <Trans
          i18nKey="pages.employersDashboard.betaMessage"
          components={{
            "user-feedback-link": (
              <a
                href={routes.external.massgov.feedbackEmployer}
                target="_blank"
                rel="noopener"
              />
            ),
          }}
        />
      </p>
    </Alert>
  );
};

DashboardInfoAlert.propTypes = {
  user: PropTypes.instanceOf(User).isRequired,
};

const Filters = (props) => {
  const { activeFilters, updateClaimsRequestParams, user } = props;
  const { t } = useTranslation();

  const handleChange = (evt) => {
    updateClaimsRequestParams([
      {
        name: evt.target.name,
        value: evt.target.value,
      },
      {
        // Reset the page to 1 since filters affect what shows on the first page
        name: "page_offset",
        value: "1",
      },
    ]);
  };

  return (
    <React.Fragment>
      {user.verifiedEmployers.length > 1 && (
        <Dropdown
          hideEmptyChoice
          choices={[
            {
              label: t("pages.employersDashboard.filterOrgsShowAllChoice"),
              value: "",
            },
            ...user.verifiedEmployers.map((employer) => ({
              label: `${employer.employer_dba} (${employer.employer_fein})`,
              value: employer.employer_id,
            })),
          ]}
          label={t("pages.employersDashboard.filterOrgsLabel")}
          smallLabel
          name="employer_id"
          onChange={handleChange}
          value={get(activeFilters, "employer_id", "")}
        />
      )}
    </React.Fragment>
  );
};

Filters.propTypes = {
  activeFilters: PropTypes.shape({
    employer_id: PropTypes.string,
  }).isRequired,
  updateClaimsRequestParams: PropTypes.func.isRequired,
  user: PropTypes.instanceOf(User).isRequired,
};

export default withClaims(Dashboard);
