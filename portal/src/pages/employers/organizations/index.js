import Alert from "../../../components/Alert";
import BackButton from "../../../components/BackButton";
import ButtonLink from "../../../components/ButtonLink";
import LeaveAdministratorRow from "../../../components/employers/LeaveAdministratorRow";
import PropTypes from "prop-types";
import React from "react";
import Table from "../../../components/Table";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import User from "../../../models/User";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

export const Index = (props) => {
  const { appLogic, query } = props;
  const { t } = useTranslation();
  const { hasVerifiableEmployer, user_leave_administrators } =
    appLogic.users.user;
  const accountConverted = query?.account_converted === "true";

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.employersOrganizations.backToDashboardLabel")}
        href={appLogic.portalFlow.getNextPageRoute("BACK")}
      />
      <Title>{t("pages.employersOrganizations.title")}</Title>
      {accountConverted && (
        <Alert
          heading={t("pages.employersOrganizations.convertHeading")}
          state="success"
        >
          {t("pages.employersOrganizations.convertDescription")}
        </Alert>
      )}
      {hasVerifiableEmployer && (
        <Alert
          state="warning"
          heading={t("pages.employersOrganizations.verificationTitle")}
        >
          <p>
            <Trans
              i18nKey="pages.employersOrganizations.verificationBody"
              components={{
                "your-organizations-link": <React.Fragment />,
              }}
            />
          </p>
        </Alert>
      )}
      <p data-test="future-availability-message">
        {t("pages.employersOrganizations.nearFutureAvailability")}
      </p>

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
              <td>{t("shared.noneReported")}</td>
              <td />
            </tr>
          )}
        </tbody>
      </Table>
      <ButtonLink href={routes.employers.addOrganization}>
        {t("pages.employersOrganizations.addOrganizationButton")}
      </ButtonLink>
    </React.Fragment>
  );
};

Index.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
    }).isRequired,
    users: PropTypes.shape({
      user: PropTypes.instanceOf(User).isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    account_converted: PropTypes.string,
  }),
};

export default withUser(Index);
