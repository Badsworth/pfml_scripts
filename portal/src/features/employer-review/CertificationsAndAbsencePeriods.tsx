import { ClaimDocument, DocumentType } from "../../models/Document";
import { AbsencePeriod } from "../../models/AbsencePeriod";
import DownloadableDocument from "../../components/DownloadableDocument";
import EmployerClaim from "../../models/EmployerClaim";
import Heading from "../../components/core/Heading";
import LeaveReason from "../../models/LeaveReason";
import PaginatedAbsencePeriodsTable from "./PaginatedAbsencePeriodsTable";
import React from "react";
import ReviewHeading from "../../components/ReviewHeading";
import ReviewRow from "../../components/ReviewRow";
import { Trans } from "react-i18next";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

interface CertificationsAndAbsencePeriodsProps {
  claim: EmployerClaim;
  documents: ClaimDocument[];
  downloadDocument: (
    document: ClaimDocument,
    absenceId: string
  ) => Promise<Blob | undefined>;
}

const CertificationsAndAbsencePeriods = (
  props: CertificationsAndAbsencePeriodsProps
) => {
  const { t } = useTranslation();
  const absencePeriodsByReason = AbsencePeriod.groupByReason(
    AbsencePeriod.sortNewToOld(props.claim.absence_periods)
  );

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("components.employersCertsAndPeriods.header")}
      </ReviewHeading>

      {props.documents.length > 0 && (
        <ReviewRow
          level="3"
          label={t("components.employersCertsAndPeriods.documentationLabel")}
        >
          <Trans
            i18nKey="components.employersCertsAndPeriods.recordkeepingInstructions"
            components={{
              "mass-employer-role-link": (
                <a
                  href={routes.external.massgov.employersGuide}
                  target="_blank"
                  rel="noopener"
                />
              ),
            }}
          />
          <ul className="usa-list">
            {props.documents.map((document) => (
              <li key={document.fineos_document_id}>
                <DownloadableDocument
                  absenceId={props.claim.fineos_absence_id}
                  displayDocumentName={t(
                    "components.employersCertsAndPeriods.documentName"
                  )}
                  document={document}
                  downloadClaimDocument={props.downloadDocument}
                  showCreatedAt
                />
                {document.document_type ===
                  DocumentType.certification[LeaveReason.care] && (
                  <div className="text-base-dark">
                    {t(
                      "components.employersCertsAndPeriods.caringLeaveDocumentInstructions"
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </ReviewRow>
      )}

      <ReviewRow
        level="3"
        label={t("components.employersCertsAndPeriods.leaveDurationLabel")}
      >
        {formatDateRange(props.claim.leaveStartDate, props.claim.leaveEndDate)}
      </ReviewRow>

      {Object.keys(absencePeriodsByReason).map((reason) => (
        <div
          className="margin-top-6"
          key={reason}
          data-testid="absence periods"
        >
          <Heading level="3">
            {t("components.employersCertsAndPeriods.reasonHeading", {
              context: findKeyByValue(LeaveReason, reason),
            })}
          </Heading>
          <PaginatedAbsencePeriodsTable
            absencePeriods={absencePeriodsByReason[reason]}
          />
        </div>
      ))}
    </React.Fragment>
  );
};

export default CertificationsAndAbsencePeriods;
