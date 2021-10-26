import React, { useEffect } from "react";

import { AbsenceCaseStatus } from "../../../models/Claim";
import AbsenceCaseStatusTag from "../../../components/AbsenceCaseStatusTag";
import { AppLogic } from "../../../hooks/useAppLogic";
import BackButton from "../../../components/BackButton";
import { DocumentType } from "../../../models/Document";
import DownloadableDocument from "../../../components/DownloadableDocument";
import EmployerClaim from "../../../models/EmployerClaim";
import Heading from "../../../components/Heading";
import Lead from "../../../components/Lead";
import LeaveReason from "../../../models/LeaveReason";
import StatusRow from "../../../components/StatusRow";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import findDocumentsByTypes from "../../../utils/findDocumentsByTypes";
import findKeyByValue from "../../../utils/findKeyByValue";
import formatDateRange from "../../../utils/formatDateRange";
import { get } from "lodash";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";
import withEmployerClaim from "../../../hoc/withEmployerClaim";

interface StatusProps {
  appLogic: AppLogic;
  claim: EmployerClaim;
  query: {
    absence_id: string;
  };
}

export const Status = (props: StatusProps) => {
  const {
    appLogic,
    claim,
    query: { absence_id: absenceId },
  } = props;
  const {
    employers: { claimDocumentsMap, downloadDocument },
  } = appLogic;
  const { isContinuous, isIntermittent, isReducedSchedule } = claim;
  const { t } = useTranslation();

  useEffect(() => {
    appLogic.employers.loadDocuments(absenceId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [absenceId]);

  const allDocuments = claimDocumentsMap.get(absenceId)?.items || [];
  const legalNotices = findDocumentsByTypes(allDocuments, [
    DocumentType.approvalNotice,
    DocumentType.denialNotice,
    DocumentType.requestForInfoNotice,
    DocumentType.withdrawalNotice,
    DocumentType.appealAcknowledgment,
  ]);

  return (
    <React.Fragment>
      <BackButton />
      <Title>
        {t("pages.employersClaimsStatus.title", { name: claim.fullName })}
      </Title>
      <Lead>
        <Trans
          i18nKey="pages.employersClaimsStatus.lead"
          tOptions={{
            context: findKeyByValue(AbsenceCaseStatus, claim.status)
              ? "decision"
              : // Pending claims refer to applications that are partially submitted (Part 1 only), awaiting employer response, or awaiting adjudication
                "pending",
          }}
          components={{
            "dfml-regulations-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.dfmlRegulations}
              />
            ),
          }}
        />
      </Lead>
      <Heading level="2">
        {t("pages.employersClaimsStatus.leaveDetailsLabel")}
      </Heading>
      <StatusRow label={t("pages.employersClaimsStatus.applicationIdLabel")}>
        {absenceId}
      </StatusRow>
      <StatusRow label={t("pages.employersClaimsStatus.statusLabel")}>
        <AbsenceCaseStatusTag status={claim.status} />
      </StatusRow>
      <StatusRow label={t("pages.employersClaimsStatus.leaveReasonLabel")}>
        {t("pages.employersClaimsStatus.leaveReasonValue", {
          context: findKeyByValue(
            LeaveReason,
            get(claim, "leave_details.reason")
          ),
        })}
      </StatusRow>
      <StatusRow label={t("pages.employersClaimsStatus.leaveDurationLabel")}>
        {formatDateRange(claim.leaveStartDate, claim.leaveEndDate)}
      </StatusRow>
      {isContinuous && (
        <StatusRow
          label={t("pages.employersClaimsStatus.leaveDurationLabel_continuous")}
        >
          {claim.continuousLeaveDateRange()}
        </StatusRow>
      )}
      {isReducedSchedule && (
        <StatusRow
          label={t("pages.employersClaimsStatus.leaveDurationLabel_reduced")}
        >
          {claim.reducedLeaveDateRange()}
        </StatusRow>
      )}
      {isIntermittent && (
        <StatusRow
          label={t(
            "pages.employersClaimsStatus.leaveDurationLabel_intermittent"
          )}
        >
          {claim.intermittentLeaveDateRange()}
        </StatusRow>
      )}
      {legalNotices.length > 0 && (
        <div className="border-top-2px border-base-lighter padding-top-2">
          <Heading level="2">
            {t("pages.employersClaimsStatus.noticesLabel")}
          </Heading>
          <ul
            className="usa-list usa-list--unstyled margin-top-2"
            data-testid="documents"
          >
            {legalNotices.map((document) => (
              <li key={document.fineos_document_id} className="margin-bottom-2">
                <DownloadableDocument
                  absenceId={absenceId}
                  downloadClaimDocument={downloadDocument}
                  document={document}
                  showCreatedAt
                />
              </li>
            ))}
          </ul>
        </div>
      )}
    </React.Fragment>
  );
};

export default withEmployerClaim(Status);
