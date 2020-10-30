import Claim, { LeaveReason } from "../../../models/Claim";
import React, { useEffect } from "react";
import { Trans, useTranslation } from "react-i18next";
import AppErrorInfo from "../../../models/AppErrorInfo";
import AppErrorInfoCollection from "../../../models/AppErrorInfoCollection";
import BackButton from "../../../components/BackButton";
import Heading from "../../../components/Heading";
import Lead from "../../../components/Lead";
import PropTypes from "prop-types";
import Spinner from "../../../components/Spinner";
import StatusTag from "../../../components/StatusTag";
import Title from "../../../components/Title";
import findKeyByValue from "../../../utils/findKeyByValue";
import formatDateRange from "../../../utils/formatDateRange";
import { get } from "lodash";
import withUser from "../../../hoc/withUser";

export const Status = (props) => {
  const {
    appLogic,
    query: { absence_id: absenceId },
    retrievedClaim,
  } = props;
  const { t } = useTranslation();
  const claim = retrievedClaim || appLogic.employers.claim;

  if (!absenceId) {
    appLogic.setAppErrors(
      new AppErrorInfoCollection(
        new AppErrorInfo("No 'absence_id' found in the query params.")
      )
    );
  }

  useEffect(() => {
    if (!claim) {
      appLogic.employers.load(absenceId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claim, absenceId]);

  const documentPostedDate = formatDateRange("2021-01-22");

  return (
    <React.Fragment>
      {!claim && appLogic.appErrors.isEmpty && (
        <div className="margin-top-8 text-center">
          <Spinner aria-valuetext={t("components.spinner.label")} />
        </div>
      )}

      {claim && (
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
            <StatusRow
              label={t("pages.employersClaimsStatus.applicationIdLabel")}
            >
              {absenceId}
            </StatusRow>
            <StatusRow label={t("pages.employersClaimsStatus.statusLabel")}>
              <StatusTag state="approved" />
            </StatusRow>
            <StatusRow
              label={t("pages.employersClaimsStatus.leaveReasonLabel")}
            >
              {t("pages.employersClaimsStatus.leaveReasonValue", {
                context: findKeyByValue(
                  LeaveReason,
                  get(claim, "leave_details.reason")
                ),
              })}
            </StatusRow>
            <StatusRow
              label={t("pages.employersClaimsStatus.leaveDurationLabel")}
            >
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
      )}
    </React.Fragment>
  );
};

Status.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
    employers: PropTypes.shape({
      load: PropTypes.func.isRequired,
      claim: PropTypes.instanceOf(Claim),
    }).isRequired,
    setAppErrors: PropTypes.func.isRequired,
  }).isRequired,
  query: PropTypes.shape({
    absence_id: PropTypes.string,
  }).isRequired,
  retrievedClaim: PropTypes.instanceOf(Claim),
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
