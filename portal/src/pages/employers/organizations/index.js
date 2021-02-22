import Alert from "../../../components/Alert";
import BackButton from "../../../components/BackButton";
import LeaveAdministratorRow from "../../../components/employers/LeaveAdministratorRow";
import PropTypes from "prop-types";
import React from "react";
import Table from "../../../components/Table";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import User from "../../../models/User";
import { isFeatureEnabled } from "../../../services/featureFlags";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

export const Index = ({ appLogic }) => {
  const { t } = useTranslation();
  const {
    hasVerifiableEmployer,
    user_leave_administrators,
  } = appLogic.users.user;
  const showVerifications = isFeatureEnabled("employerShowVerifications");

  return (
    <React.Fragment>
      <BackButton />
      <Title>{t("pages.employersOrganizations.title")}</Title>
      {showVerifications && hasVerifiableEmployer && (
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
                leaveAdmin={leaveAdmin}
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

Index.propTypes = {
  appLogic: PropTypes.shape({
    users: PropTypes.shape({
      user: PropTypes.instanceOf(User).isRequired,
    }).isRequired,
  }).isRequired,
};

export default withUser(Index);
