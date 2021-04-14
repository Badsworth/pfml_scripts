import Alert from "../../components/Alert";
import ClaimCollection from "../../models/ClaimCollection";
import EmployerNavigationTabs from "../../components/employers/EmployerNavigationTabs";
import PropTypes from "prop-types";
import React from "react";
import Table from "../../components/Table";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import User from "../../models/User";
import formatDateRange from "../../utils/formatDateRange";
import { get } from "lodash";
import { isFeatureEnabled } from "../../services/featureFlags";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaims from "../../hoc/withClaims";

export const Dashboard = (props) => {
  const { appLogic, user } = props;
  const shouldShowDashboard = isFeatureEnabled("employerShowDashboard");
  const shouldShowVerifications = isFeatureEnabled("employerShowVerifications");
  const { t } = useTranslation();

  if (!shouldShowDashboard) {
    appLogic.portalFlow.goTo(routes.employers.welcome);
  }

  const hasOnlyUnverifiedEmployers = user.hasOnlyUnverifiedEmployers;
  const hasVerifiableEmployer = user.hasVerifiableEmployer;
  const showVerificationRowInPlaceOfClaims =
    shouldShowVerifications && hasOnlyUnverifiedEmployers;

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

  return (
    <React.Fragment>
      <EmployerNavigationTabs activePath={appLogic.portalFlow.pathname} />
      <Title>{t("pages.employersDashboard.title")}</Title>
      {shouldShowVerifications && hasVerifiableEmployer && (
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
      <p className="margin-bottom-4">
        {t("pages.employersDashboard.instructions")}
      </p>

      <Table className="width-full tablet:width-auto" responsive scrollable>
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
          {showVerificationRowInPlaceOfClaims && (
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
          {!showVerificationRowInPlaceOfClaims && (
            <ClaimTableRows
              claims={props.claims}
              tableColumnKeys={tableColumnKeys}
            />
          )}
        </tbody>
      </Table>
    </React.Fragment>
  );
};

Dashboard.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
  claims: PropTypes.instanceOf(ClaimCollection),
  user: PropTypes.instanceOf(User).isRequired,
};

/**
 * Renders the <tr> elements for each claim, or a message indicating
 * no claim data exists
 */
const ClaimTableRows = (props) => {
  const { claims, tableColumnKeys } = props;
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
    // New Application page handles conditional routing for claims (if is not reviewable, navigates to Status page)
    const infoRequestRoute = routeWithParams("employers.newApplication", {
      absence_id: get(claim, "fineos_absence_id"),
    });

    switch (columnKey) {
      case "created_at":
        return formatDateRange(get(claim, columnKey));
      case "fineos_absence_id":
        return <a href={infoRequestRoute}>{get(claim, columnKey)}</a>;
      case "employee_name":
        return <a href={infoRequestRoute}>{get(claim, "employee.fullName")}</a>;
      case "employer_dba":
        return get(claim, "employer.employer_dba");
      case "employer_fein":
        return get(claim, "employer.employer_fein");
      case "status":
        // TODO (EMPLOYER-1125): Render a <Tag> for the status
        return "--";
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
  claims: Dashboard.propTypes.claims,
  tableColumnKeys: PropTypes.arrayOf(PropTypes.string).isRequired,
};

export default withClaims(Dashboard);
