import {
  BenefitsApplicationDocument,
  DocumentType,
  findDocumentsByTypes,
} from "../../models/Document";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import withClaimDocuments, {
  WithClaimDocumentsProps,
} from "../../hoc/withClaimDocuments";
import Accordion from "../../components/core/Accordion";
import AccordionItem from "../../components/core/AccordionItem";
import Alert from "../../components/core/Alert";
import DocumentRequirements from "../../components/DocumentRequirements";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/core/Heading";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import Spinner from "../../components/core/Spinner";
import { Trans } from "react-i18next";
import { get } from "lodash";
import hasDocumentsLoadError from "../../utils/hasDocumentsLoadError";
import routes from "../../routes";
import uploadDocumentsHelper from "../../utils/uploadDocumentsHelper";
import useFilesLogic from "../../hooks/useFilesLogic";
import { useTranslation } from "../../locales/i18n";

interface UploadIdProps
  extends WithClaimDocumentsProps,
    WithBenefitsApplicationProps {
  query: {
    additionalDoc?: string;
    showStateId?: string;
  };
}

export const UploadId = (props: UploadIdProps) => {
  const { t } = useTranslation();
  const { appLogic, claim, documents, isLoadingDocuments, query } = props;
  const { files, processFiles, removeFile } = useFilesLogic({
    clearErrors: appLogic.clearErrors,
    catchError: appLogic.catchError,
  });
  const { additionalDoc, showStateId } = query;
  const [submissionInProgress, setSubmissionInProgress] = React.useState(false);
  let hasStateId;
  if (showStateId === "true") {
    hasStateId = true;
  } else if (showStateId === "false") {
    hasStateId = false;
  } else {
    hasStateId = claim.has_state_id;
  }
  const contentContext = hasStateId ? "mass" : "other";
  const absence_id = get(claim, "fineos_absence_id");

  const { errors, portalFlow } = appLogic;
  const hasLoadingDocumentsError = hasDocumentsLoadError(
    errors,
    claim.application_id
  );

  const idDocuments = findDocumentsByTypes<BenefitsApplicationDocument>(
    documents,
    [DocumentType.identityVerification]
  );

  const handleSave = async () => {
    if (files.isEmpty && idDocuments.length) {
      // Allow user to skip this page if they've previously uploaded documents
      portalFlow.goToNextPage({ claim }, { claim_id: claim.application_id });
      return;
    }
    setSubmissionInProgress(true);
    const uploadPromises = appLogic.documents.attach(
      claim.application_id,
      files.items,
      DocumentType.identityVerification,
      additionalDoc === "true"
    );

    const { success } = await uploadDocumentsHelper(
      uploadPromises,
      files,
      removeFile
    );
    setSubmissionInProgress(false);
    if (success) {
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
      buttonLoadingMessage={t("pages.claimsUploadId.uploadingMessage")}
      title={t("pages.claimsUploadId.title")}
      onSave={handleSave}
    >
      <div className="measure-6">
        <Heading level="2" size="1">
          {t("pages.claimsUploadId.sectionLabel", { context: contentContext })}
        </Heading>
        <DocumentRequirements type="id" />
        {!hasStateId && (
          <div className="border-bottom border-base-light margin-bottom-4 padding-bottom-4">
            <Trans
              i18nKey="pages.claimsUploadId.otherIdentityDocs"
              components={{
                ul: <ul className="usa-list" />,
                li: <li />,
                "work-visa-link": (
                  <a
                    href={routes.external.workVisa}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
              }}
            />

            <Accordion>
              <AccordionItem
                heading={t("pages.claimsUploadId.accordionHeading")}
              >
                <Trans
                  i18nKey="pages.claimsUploadId.accordionContent"
                  components={{
                    ul: <ul className="usa-list" />,
                    li: <li />,
                    "identity-proof-link": (
                      <a
                        href={routes.external.massgov.identityProof}
                        rel="noopener noreferrer"
                        target="_blank"
                      />
                    ),
                    "puerto-rican-birth-certificate-link": (
                      <a
                        href={routes.external.puertoRicanBirthCertificate}
                        rel="noopener noreferrer"
                        target="_blank"
                      />
                    ),
                  }}
                />
              </AccordionItem>
            </Accordion>
          </div>
        )}
        <FileUploadDetails />

        {hasLoadingDocumentsError && (
          <Alert className="margin-bottom-3" noIcon>
            <Trans
              i18nKey="pages.claimsUploadId.documentsLoadError"
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
            documents={idDocuments}
            onChange={processFiles}
            disableRemove={submissionInProgress}
            onRemoveTempFile={removeFile}
            fileHeadingPrefix={t("pages.claimsUploadId.fileHeadingPrefix")}
            addFirstFileButtonText={t(
              "pages.claimsUploadId.addFirstFileButton"
            )}
            addAnotherFileButtonText={t(
              "pages.claimsUploadId.addAnotherFileButton"
            )}
          />
        )}
      </div>
    </QuestionPage>
  );
};

export default withBenefitsApplication(withClaimDocuments(UploadId));
