import EmployerClaim, {
  FineosLeaveReason,
} from "../../../models/EmployerClaim";
import { Trans, useTranslation } from "react-i18next";
import BackButton from "../../../components/BackButton";
import Heading from "../../../components/Heading";
import Lead from "../../../components/Lead";
import PropTypes from "prop-types";
import React from "react";
import StatusRow from "../../../components/StatusRow";
import StatusTag from "../../../components/StatusTag";
import Title from "../../../components/Title";
import findKeyByValue from "../../../utils/findKeyByValue";
import formatDateRange from "../../../utils/formatDateRange";
import { get } from "lodash";
import withEmployerClaim from "../../../hoc/withEmployerClaim";

export const Status = (props) => {
  const {
    appLogic: {
      employers: { claim },
    },
    query: { absence_id: absenceId },
  } = props;
  const { t } = useTranslation();

  const documentPostedDate = formatDateRange("2021-01-22");

  return (
    <React.Fragment>
      <BackButton />
      <Title>
        {t("pages.employersClaimsStatus.title", { name: claim.fullName })}
      </Title>
      <Lead>
        <Trans i18nKey="pages.employersClaimsStatus.lead" />
      </Lead>
      <Heading level="2">
        {t("pages.employersClaimsStatus.leaveDetailsLabel")}
      </Heading>
      <div className="border-bottom-2px border-base-lighter">
        <StatusRow label={t("pages.employersClaimsStatus.applicationIdLabel")}>
          {absenceId}
        </StatusRow>
        <StatusRow label={t("pages.employersClaimsStatus.statusLabel")}>
          <StatusTag state="approved" />
        </StatusRow>
        <StatusRow label={t("pages.employersClaimsStatus.leaveReasonLabel")}>
          {t("pages.employersClaimsStatus.leaveReasonValue", {
            context: findKeyByValue(
              FineosLeaveReason,
              get(claim, "leave_details.reason")
            ),
          })}
        </StatusRow>
        <StatusRow label={t("pages.employersClaimsStatus.leaveDurationLabel")}>
          {formatDateRange(claim.leaveStartDate, claim.leaveEndDate)}
        </StatusRow>
      </div>
      <Heading level="2">
        {t("pages.employersClaimsStatus.noticesLabel")}
      </Heading>
      {/* TODO (EMPLOYER-355) fetch real documents */}
      <div>
        <p>
          <a href="/">Benefit determination notice (PDF)</a>
        </p>
        <p className="margin-top-1">
          {t("pages.employersClaimsStatus.documentPostedDate", {
            date: documentPostedDate,
          })}
        </p>
      </div>
    </React.Fragment>
  );
};

Status.propTypes = {
  appLogic: PropTypes.shape({
    employers: PropTypes.shape({
      claim: PropTypes.instanceOf(EmployerClaim),
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    absence_id: PropTypes.string,
  }).isRequired,
};

export default withEmployerClaim(Status);
