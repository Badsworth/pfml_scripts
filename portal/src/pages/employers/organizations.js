import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import PropTypes from "prop-types";
import React from "react";
import Table from "../../components/Table";
import Tag from "../../components/Tag";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import User from "../../models/User";
import { isFeatureEnabled } from "../../services/featureFlags";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withUser from "../../hoc/withUser";

export const Organizations = ({ appLogic }) => {
  const { t } = useTranslation();
  const {
    hasUnverifiedEmployer,
    user_leave_administrators,
  } = appLogic.users.user;
  const showVerifications = isFeatureEnabled("employerShowVerifications");

  return (
    <React.Fragment>
      <BackButton />
      <Title>{t("pages.employersOrganizations.title")}</Title>
      {showVerifications && hasUnverifiedEmployer && (
        <Alert
          state="warning"
          heading={t("pages.employersDashboard.verificationTitle")}
        >
          <p>
            <Trans
              i18nKey="pages.employersDashboard.verificationBody"
              components={{
                "your-organizations-link": <React.Fragment />,
              }}
            />
          </p>
        </Alert>
      )}
      <p>{t("pages.employersOrganizations.nearFutureAvailability")}</p>

      <Table responsive className="width-full">
        <thead>
          <tr>
            <th scope="col">
              {t("pages.employersOrganizations.organizationsTableHeader")}
            </th>
            <th scope="col">
              {t("pages.employersOrganizations.einTableHeader")}
            </th>
          </tr>
        </thead>
        <tbody>
          {user_leave_administrators.length > 0 &&
            user_leave_administrators.map((leaveAdmin) => (
              <LeaveAdministratorRow
                key={leaveAdmin.employer_id}
                {...leaveAdmin}
              />
            ))}
          {user_leave_administrators.length === 0 && (
            <tr>
              <th scope="row" colSpan={2}>
                <span>{t("shared.noneReported")}</span>
              </th>
            </tr>
          )}
        </tbody>
      </Table>
    </React.Fragment>
  );
};

Organizations.propTypes = {
  appLogic: PropTypes.shape({
    users: PropTypes.shape({
      user: PropTypes.instanceOf(User).isRequired,
    }).isRequired,
  }).isRequired,
};

const LeaveAdministratorRow = ({
  employer_dba,
  employer_fein,
  employer_id,
  verified,
}) => {
  const { t } = useTranslation();
  const shouldShowVerificationPrompts =
    isFeatureEnabled("employerShowVerifications") && !verified;

  const employerDbaTag = shouldShowVerificationPrompts ? (
    // clickable variant of a table row. navigates to verify business page.
    <a
      className="margin-right-3"
      href={routeWithParams("employers.verifyBusiness", {
        employer_id,
        next: routes.employers.organizations,
      })}
    >
      {employer_dba}
    </a>
  ) : (
    // non-clickable variant of a table row.
    <span className="margin-right-3">{employer_dba}</span>
  );

  return (
    <tr>
      <th
        scope="row"
        data-label={t("pages.employersOrganizations.organizationsTableHeader")}
      >
        {employerDbaTag}
        {shouldShowVerificationPrompts && (
          <Tag
            label={t("pages.employersOrganizations.verificationRequired")}
            state="warning"
          />
        )}
      </th>
      <td data-label={t("pages.employersOrganizations.einTableHeader")}>
        {employer_fein}
      </td>
    </tr>
  );
};

LeaveAdministratorRow.propTypes = {
  employer_dba: PropTypes.string.isRequired,
  employer_fein: PropTypes.string.isRequired,
  employer_id: PropTypes.string.isRequired,
  verified: PropTypes.bool.isRequired,
};

export default withUser(Organizations);
