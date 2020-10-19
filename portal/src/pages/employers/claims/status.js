import { Trans, useTranslation } from "react-i18next";
import BackButton from "../../../components/BackButton";
import Heading from "../../../components/Heading";
import Lead from "../../../components/Lead";
import { MockClaimBuilder } from "../../../../tests/test-utils";
import PropTypes from "prop-types";
import React from "react";
import StatusTag from "../../../components/StatusTag";
import Title from "../../../components/Title";
import User from "../../../models/User";
import formatDateRange from "../../../utils/formatDateRange";
import withUser from "../../../hoc/withUser";

// TODO (EMPLOYER-453) substitute with real data
const MOCK_CLAIM = new MockClaimBuilder()
  .verifiedId()
  .continuous()
  .submitted()
  .create();

export const Status = (props) => {
  const { t } = useTranslation();

  const {
    application_id,
    // TODO (EMPLOYER-453) handle intermittent leave periods
    leave_details: { continuous_leave_periods },
  } = MOCK_CLAIM;
  const { start_date, end_date } = continuous_leave_periods[0];
  const documentPostedDate = formatDateRange("2021-01-22");

  return (
    <React.Fragment>
      <BackButton />
      <Title>
        {t("pages.employersClaimStatus.title", { name: MOCK_CLAIM.fullName })}
      </Title>
      <Lead>
        <Trans i18nKey="pages.employersClaimStatus.lead" />
      </Lead>
      <Heading level="2">
        {t("pages.employersClaimStatus.leaveDetailsLabel")}
      </Heading>
      <div className="border-bottom-2px border-base-lighter">
        <StatusRow label={t("pages.employersClaimStatus.applicationIdLabel")}>
          {application_id}
        </StatusRow>
        <StatusRow label={t("pages.employersClaimStatus.statusLabel")}>
          <StatusTag state="approved" />
        </StatusRow>
        <StatusRow label={t("pages.employersClaimStatus.leaveTypeLabel")}>
          {/* TODO (EMPLOYER-453) consider other types of leave */}
          {t("pages.employersClaimStatus.medicalLeave")}
        </StatusRow>
        <StatusRow label={t("pages.employersClaimStatus.leaveDurationLabel")}>
          {/* TODO (EMPLOYER-453) handle multiple leave periods */}
          {formatDateRange(start_date, end_date)}
        </StatusRow>
      </div>
      <Heading level="2">
        {t("pages.employersClaimStatus.noticesLabel")}
      </Heading>
      {/* TODO (EMPLOYER-355) fetch real documents */}
      <div>
        <p>
          <a href="/">Benefit determination notice (PDF)</a>
        </p>
        <p className="margin-top-1">
          {t("pages.employersClaimStatus.documentPostedDate", {
            date: documentPostedDate,
          })}
        </p>
      </div>
    </React.Fragment>
  );
};

Status.propTypes = {
  appLogic: PropTypes.shape({
    users: PropTypes.shape({
      user: PropTypes.instanceOf(User).isRequired,
    }).isRequired,
  }).isRequired,
};

export const StatusRow = ({ children, label }) => {
  return (
    <div className="margin-bottom-2 padding-bottom-2">
      <Heading level="3" size="4" className="margin-bottom-1">
        {label}
      </Heading>
      {children}
    </div>
  );
};

StatusRow.propTypes = {
  children: PropTypes.node.isRequired,
  label: PropTypes.node.isRequired,
};

export default withUser(Status);
