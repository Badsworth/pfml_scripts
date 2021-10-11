import React, { useEffect } from "react";

import { AbsenceCaseStatus } from "../../../models/Claim";
import AbsenceCaseStatusTag from "../../../components/AbsenceCaseStatusTag";
import BackButton from "../../../components/BackButton";
import DocumentCollection from "../../../models/DocumentCollection";
import { DocumentType } from "../../../models/Document";
import DownloadableDocument from "../../../components/DownloadableDocument";
import EmployerClaim from "../../../models/EmployerClaim";
import Heading from "../../../components/Heading";
import Lead from "../../../components/Lead";
import LeaveReason from "../../../models/LeaveReason";
import PropTypes from "prop-types";
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

export const Status = (props) => {
  const {
    appLogic,
    query: { absence_id: absenceId },
  } = props;
  const {
    employers: { claim, documents, downloadDocument },
  } = appLogic;
  const { isContinuous, isIntermittent, isReducedSchedule } = claim;
  const { t } = useTranslation();

  useEffect(() => {
    if (!documents) {
      appLogic.employers.loadDocuments(absenceId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documents, absenceId]);

  const allDocuments = documents ? documents.items : [];
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
        {/* @ts-expect-error ts-migrate(2786) FIXME: 'AbsenceCaseStatusTag' cannot be used as a JSX com... Remove this comment to see the full error message */}
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
      {/* TODO (EMPLOYER-448): Show leave duration and the intermittent leave period dates when API returns them to Portal */}
      {!isIntermittent && (
        <StatusRow label={t("pages.employersClaimsStatus.leaveDurationLabel")}>
          {/* @ts-expect-error ts-migrate(2554) FIXME: Expected 3 arguments, but got 2. */}
          {formatDateRange(claim.leaveStartDate, claim.leaveEndDate)}
        </StatusRow>
      )}
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
                  onDownloadClick={downloadDocument}
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

Status.propTypes = {
  appLogic: PropTypes.shape({
    employers: PropTypes.shape({
      claim: PropTypes.instanceOf(EmployerClaim),
      documents: PropTypes.instanceOf(DocumentCollection),
      downloadDocument: PropTypes.func.isRequired,
      loadDocuments: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    absence_id: PropTypes.string,
  }).isRequired,
};

export default withEmployerClaim(Status);
