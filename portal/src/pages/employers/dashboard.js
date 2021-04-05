import Alert from "../../components/Alert";
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
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withUser from "../../hoc/withUser";

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

  /**
   * Columns rendered in the table.
   * Used for rendering header labels and the field(s) in each column. These
   * mostly mirror the name of the fields rendered, but not exactly
   * since some columns might require multiple fields.
   * @type {string[]}
   */
  const tableColumnKeys = [
    "employee_name",
    "fineos_absence_id",
    "employer_dba",
    "employer_fein",
    "created_at",
    "status",
  ];

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
  // TODO (EMPLOYER-858): Change to more specific PropTypes.instanceOf once we
  // know what the API response looks like, which informs the model we use
  claims: PropTypes.arrayOf(PropTypes.object),
  user: PropTypes.instanceOf(User).isRequired,
};

/**
 * Renders the <tr> elements for each claim, or a message indicating
 * no claim data exists
 */
const ClaimTableRows = (props) => {
  const { claims, tableColumnKeys } = props;
  const { t } = useTranslation();

  if (!claims.length) {
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
    switch (columnKey) {
      case "created_at":
        return formatDateRange(get(claim, columnKey));
      case "fineos_absence_id":
        // TODO (EMPLOYER-858): Make this routing actually work
        return <a href="#">{get(claim, columnKey)}</a>;
      case "employee_name":
        // TODO (EMPLOYER-858): Use a fullName getter on the claim instance
        // TODO (EMPLOYER-858): Make this routing actually work
        return (
          <a href="#">
            {[get(claim, "first_name"), get(claim, "last_name")].join(" ")}
          </a>
        );
      case "status":
        // TODO (EMPLOYER-858): Render a <Tag> for the status
        return "--";
      default:
        return get(claim, columnKey);
    }
  };

  return claims.map((claim) => (
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

export default withUser(Dashboard);
