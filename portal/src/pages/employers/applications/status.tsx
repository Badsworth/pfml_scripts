import { DocumentType, findDocumentsByTypes } from "../../../models/Document";
import React, { useEffect } from "react";
import withEmployerClaim, {
  WithEmployerClaimProps,
} from "../../../hoc/withEmployerClaim";

import { AbsenceCaseStatus } from "../../../models/Claim";
import AbsenceCaseStatusTag from "../../../components/AbsenceCaseStatusTag";
import BackButton from "../../../components/BackButton";
import DownloadableDocument from "../../../components/DownloadableDocument";
import Heading from "../../../components/core/Heading";
import Lead from "../../../components/core/Lead";
import LeaveReason from "../../../models/LeaveReason";
import StatusRow from "../../../components/StatusRow";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import findKeyByValue from "../../../utils/findKeyByValue";
import formatDateRange from "../../../utils/formatDateRange";
import { get } from "lodash";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

export const Status = (props: WithEmployerClaimProps) => {
  const { appLogic, claim } = props;
  const {
    employers: { claimDocumentsMap, downloadDocument },
  } = appLogic;
  const { isContinuous, isIntermittent, isReducedSchedule } = claim;
  const { t } = useTranslation();

  const absenceId = claim.fineos_absence_id;

  useEffect(() => {
    appLogic.employers.loadDocuments(claim.fineos_absence_id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [absenceId]);

  const allDocuments = claimDocumentsMap.get(absenceId)?.items || [];
  const legalNotices = findDocumentsByTypes(allDocuments, [
    DocumentType.approvalNotice,
    DocumentType.denialNotice,
    DocumentType.requestForInfoNotice,
    DocumentType.withdrawalNotice,
    DocumentType.appealAcknowledgment,
    DocumentType.maximumWeeklyBenefitChangeNotice,
    DocumentType.benefitAmountChangeNotice,
    DocumentType.leaveAllotmentChangeNotice,
    DocumentType.approvedTimeCancelled,
    DocumentType.changeRequestApproved,
    DocumentType.changeRequestDenied,
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
        {/* Wrapped with margin-0 to collapse awkward default spacing between the heading and the tag */}
        <div className="margin-0">
          <AbsenceCaseStatusTag
            managedRequirements={claim.managed_requirements}
            status={claim.status}
          />
        </div>
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
