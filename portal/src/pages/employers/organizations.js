import BackButton from "../../components/BackButton";
import PropTypes from "prop-types";
import React from "react";
import Table from "../../components/Table";
import Tag from "../../components/Tag";
import Title from "../../components/Title";
import User from "../../models/User";
import { useTranslation } from "../../locales/i18n";
import withUser from "../../hoc/withUser";

export const Organizations = ({ appLogic }) => {
  const { t } = useTranslation();
  const { user_leave_administrators } = appLogic.users.user;

  return (
    <React.Fragment>
      <BackButton />
      <Title>{t("pages.employersOrganizations.title")}</Title>
      <p>{t("pages.employersOrganizations.nearFutureAvailability")}</p>
      <Table className="width-full">
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
              <th scope="row">
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

const LeaveAdministratorRow = ({ employer_dba, employer_fein, verified }) => {
  const { t } = useTranslation();
  const employerDbaClassName = !verified ? "margin-right-3" : undefined;

  return (
    <tr>
      <th scope="row">
        <span className={employerDbaClassName}>{employer_dba}</span>
        {!verified && (
          <Tag
            label={t("pages.employersOrganizations.verificationRequired")}
            state="warning"
          />
        )}
      </th>
      <td>{employer_fein}</td>
    </tr>
  );
};

LeaveAdministratorRow.propTypes = {
  employer_dba: PropTypes.string.isRequired,
  employer_fein: PropTypes.string.isRequired,
  verified: PropTypes.bool.isRequired,
};

export default withUser(Organizations);
