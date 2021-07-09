import PropTypes from "prop-types";
import React from "react";
import Tag from "../Tag";
import { UserLeaveAdministrator } from "../../models/User";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

export const LeaveAdministratorRow = ({ leaveAdmin }) => {
  const {
    employer_dba,
    employer_fein,
    employer_id,
    has_verification_data,
    verified,
  } = leaveAdmin;
  const { t } = useTranslation();
  const isVerificationRequired = !verified && has_verification_data;
  const isVerificationBlocked = !verified && !has_verification_data;

  let verificationLink;
  let verificationTag;

  if (isVerificationRequired) {
    verificationLink = routeWithParams("employers.verifyContributions", {
      employer_id,
      next: routes.employers.organizations,
    });
    verificationTag = (
      <a href={verificationLink}>
        <Tag
          label={t("pages.employersOrganizations.verificationRequired")}
          state="warning"
        />
      </a>
    );
  } else if (isVerificationBlocked) {
    verificationLink = routeWithParams("employers.cannotVerify", {
      employer_id,
    });
    verificationTag = (
      <a href={verificationLink}>
        <Tag
          label={t("pages.employersOrganizations.verificationBlocked")}
          state="error"
        />
      </a>
    );
  }

  const employerDbaElement = verificationLink ? (
    // clickable variant of a table row. navigates to verify business page.
    <a className="margin-right-3" href={verificationLink}>
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
        {employerDbaElement}
        {verificationTag}
      </th>
      <td data-label={t("pages.employersOrganizations.einTableHeader")}>
        {employer_fein}
      </td>
    </tr>
  );
};

LeaveAdministratorRow.propTypes = {
  leaveAdmin: PropTypes.instanceOf(UserLeaveAdministrator),
};

export default LeaveAdministratorRow;
