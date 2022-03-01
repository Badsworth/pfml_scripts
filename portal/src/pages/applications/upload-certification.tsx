import {
  BenefitsApplicationDocument,
  DocumentType,
  findDocumentsByLeaveReason,
} from "../../models/Document";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import withClaimDocuments, {
  WithClaimDocumentsProps,
} from "../../hoc/withClaimDocuments";
import Alert from "../../components/core/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import DocumentRequirements from "../../components/DocumentRequirements";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/core/Heading";
import Lead from "../../components/core/Lead";
import LeaveReason from "../../models/LeaveReason";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { ReasonQualifier } from "../../models/BenefitsApplication";
import Spinner from "../../components/core/Spinner";
import { Trans } from "react-i18next";
import findKeyByValue from "../../utils/findKeyByValue";
import { get } from "lodash";
import hasDocumentsLoadError from "../../utils/hasDocumentsLoadError";
import routes from "../../routes";
import uploadDocumentsHelper from "../../utils/uploadDocumentsHelper";
import useFilesLogic from "../../hooks/useFilesLogic";
import { useTranslation } from "../../locales/i18n";

interface UploadCertificationProps
  extends WithClaimDocumentsProps,
    WithBenefitsApplicationProps {
  query: {
    additionalDoc?: string;
  };
}

export const UploadCertification = (props: UploadCertificationProps) => {
  const { appLogic, claim, documents, isLoadingDocuments, query } = props;
  const { t } = useTranslation();
  const claimReason = claim.leave_details.reason;
  const claimReasonQualifier = claim.leave_details.reason_qualifier;

  const { errors, portalFlow } = appLogic;
  const { files, processFiles, removeFile } = useFilesLogic({
    clearErrors: appLogic.clearErrors,
    catchError: appLogic.catchError,
  });
  const hasLoadingDocumentsError = hasDocumentsLoadError(
    errors,
    claim.application_id
  );
  const [submissionInProgress, setSubmissionInProgress] = React.useState(false);

  const conditionalContext = {
    [LeaveReason.bonding]: {
      [ReasonQualifier.newBorn]: "bonding_newborn",
      [ReasonQualifier.adoption]: "bonding_adopt_foster",
      [ReasonQualifier.fosterCare]: "bonding_adopt_foster",
    },
    [LeaveReason.care]: "care",
    [LeaveReason.medical]: "medical",
    [LeaveReason.pregnancy]: "medical",
  };
  let leadTextContext;
  switch (claimReason) {
    case LeaveReason.medical:
    case LeaveReason.pregnancy:
    case LeaveReason.care:
      leadTextContext = conditionalContext[claimReason];
      break;
    case LeaveReason.bonding:
      leadTextContext = claimReasonQualifier
        ? conditionalContext[claimReason][claimReasonQualifier]
        : undefined;
      break;
  }

  const certificationDocuments =
    findDocumentsByLeaveReason<BenefitsApplicationDocument>(
      documents,
      get(claim, "leave_details.reason")
    );

  const handleSave = async () => {
    if (files.isEmpty && certificationDocuments.length) {
      // Allow user to skip this page if they've previously uploaded documents
      portalFlow.goToNextPage({ claim }, { claim_id: claim.application_id });
      return;
    }

    const documentType = DocumentType.certification.certificationForm;
    setSubmissionInProgress(true);

    const uploadPromises = appLogic.documents.attach(
      claim.application_id,
      files.items,
      documentType,
      query.additionalDoc === "true"
    );

    const { success } = await uploadDocumentsHelper(
      uploadPromises,
      files,
      removeFile
    );
    setSubmissionInProgress(false);

    if (success) {
      const absence_id = get(claim, "fineos_absence_id");
      portalFlow.goToNextPage(
        { claim },
        { claim_id: claim.application_id, uploadedAbsenceId: absence_id }
      );
    }
  };
  const fileErrors = errors.filter(
    (errorInfo) => errorInfo.meta && errorInfo.meta.file_id
  );

  return (
    <QuestionPage
      buttonLoadingMessage={t(
        "pages.claimsUploadCertification.uploadingMessage"
      )}
      title={t("pages.claimsUploadCertification.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsUploadCertification.sectionLabel", {
          context: findKeyByValue(LeaveReason, claimReason),
        })}
      </Heading>
      <Lead>
        <Trans
          i18nKey="pages.claimsUploadCertification.lead"
          components={{
            "healthcare-provider-form-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.healthcareProviderForm}
              />
            ),
            "caregiver-certification-form-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.caregiverCertificationForm}
              />
            ),
          }}
          tOptions={{
            context: leadTextContext,
          }}
        />
      </Lead>
      <ConditionalContent
        visible={
          claim.isBondingLeave &&
          claimReasonQualifier === ReasonQualifier.newBorn
        }
      >
        <Trans
          i18nKey="pages.claimsUploadCertification.leadListNewborn"
          components={{
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />
      </ConditionalContent>
      <DocumentRequirements type="certification" />
      <FileUploadDetails />

      {hasLoadingDocumentsError && (
        <Alert className="margin-bottom-3" noIcon>
          <Trans
            i18nKey="pages.claimsUploadCertification.documentsLoadError"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
          />
        </Alert>
      )}
      {isLoadingDocuments && !hasLoadingDocumentsError && (
        <div className="margin-top-8 text-center">
          <Spinner
            aria-label={t("components.withBenefitsApplications.loadingLabel")}
          />
        </div>
      )}
      {!isLoadingDocuments && (
        <FileCardList
          fileErrors={fileErrors}
          tempFiles={files}
          documents={certificationDocuments}
          onChange={processFiles}
          onRemoveTempFile={removeFile}
          disableRemove={submissionInProgress}
          fileHeadingPrefix={t(
            "pages.claimsUploadCertification.fileHeadingPrefix"
          )}
          addFirstFileButtonText={t(
            "pages.claimsUploadCertification.addFirstFileButton"
          )}
          addAnotherFileButtonText={t(
            "pages.claimsUploadCertification.addAnotherFileButton"
          )}
        />
      )}
    </QuestionPage>
  );
};

export default withBenefitsApplication(withClaimDocuments(UploadCertification));
