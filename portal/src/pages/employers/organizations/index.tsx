import withUser, { WithUserProps } from "../../../hoc/withUser";
import Alert from "../../../components/core/Alert";
import BackButton from "../../../components/BackButton";
import ButtonLink from "../../../components/ButtonLink";
import LeaveAdministratorRow from "../../../features/employer-review/LeaveAdministratorRow";
import React from "react";
import Table from "../../../components/core/Table";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

export const Index = (
  props: WithUserProps & { query: { account_converted?: string } }
) => {
  const { appLogic, query } = props;
  const { t } = useTranslation();
  const { hasVerifiableEmployer, user_leave_administrators } = props.user;
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

export default withUser(Index);
