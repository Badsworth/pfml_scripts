import { ClaimDocument } from "../../models/Document";
import DownloadableDocument from "../DownloadableDocument";
import EmployerClaim from "../../models/EmployerClaim";
import LeaveReason from "../../models/LeaveReason";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import { Trans } from "react-i18next";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

interface LeaveDetailsProps {
  claim: EmployerClaim;
  documents: ClaimDocument[];
  downloadDocument: (
    document: ClaimDocument,
    absenceId: string
  ) => Promise<Blob | undefined>;
}

/**
 * Display overview of a leave request
 * in the Leave Admin claim review page.
 */

const LeaveDetails = (props: LeaveDetailsProps) => {
  const { t } = useTranslation();
  const {
    claim: {
      fineos_absence_id: absenceId,
      leave_details: { reason },
    },
    documents,
    downloadDocument,
  } = props;

  const isCaringLeave = reason === LeaveReason.care;
  const isPregnancy = reason === LeaveReason.pregnancy;

  const benefitsGuideLink: { [reason: string]: string } = {
    [LeaveReason.care]: routes.external.massgov.benefitsGuide_aboutCaringLeave,
    [LeaveReason.bonding]:
      routes.external.massgov.benefitsGuide_aboutBondingLeave,
    [LeaveReason.medical]:
      routes.external.massgov.benefitsGuide_aboutMedicalLeave,
  };

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("components.employersLeaveDetails.header")}
      </ReviewHeading>
      <ReviewRow
        level="3"
        label={t("components.employersLeaveDetails.leaveTypeLabel")}
        data-test="leave-type"
      >
        {isPregnancy ? (
          t("components.employersLeaveDetails.leaveReasonValue", {
            context: findKeyByValue(LeaveReason, reason),
          })
        ) : (
          <a
            target="_blank"
            rel="noopener"
            href={reason ? benefitsGuideLink[reason] : undefined}
          >
            {t("components.employersLeaveDetails.leaveReasonValue", {
              context: findKeyByValue(LeaveReason, reason),
            })}
          </a>
        )}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("components.employersLeaveDetails.applicationIdLabel")}
      >
        {absenceId}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("components.employersLeaveDetails.leaveDurationLabel")}
      >
        {formatDateRange(props.claim.leaveStartDate, props.claim.leaveEndDate)}
      </ReviewRow>
      {!!documents.length && (
        <ReviewRow
          level="3"
          label={t("components.employersLeaveDetails.documentationLabel")}
        >
          <Trans
            i18nKey="components.employersLeaveDetails.recordkeepingInstructions"
            components={{
              "mass-employer-role-link": (
                <a
                  href={routes.external.massgov.employersGuide}
                  target="_blank"
                  rel="noopener"
                />
              ),
            }}
            tOptions={{ context: isCaringLeave ? "caringLeave" : null }}
          />
          <ul className="usa-list">
            {documents.map((document) => (
              <li key={document.fineos_document_id}>
                <DownloadableDocument
                  downloadClaimDocument={downloadDocument}
                  absenceId={absenceId}
                  document={document}
                  displayDocumentName={t(
                    "components.employersLeaveDetails.documentName"
                  )}
                />
              </li>
            ))}
          </ul>
        </ReviewRow>
      )}
    </React.Fragment>
  );
};

export default LeaveDetails;
