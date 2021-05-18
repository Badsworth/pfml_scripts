import Document, { DocumentType } from "../../models/Document";
import Accordion from "../../components/Accordion";
import AccordionItem from "../../components/AccordionItem";
import Alert from "../../components/Alert";
import DocumentRequirements from "../../components/DocumentRequirements";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/Heading";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import Spinner from "../../components/Spinner";
import { Trans } from "react-i18next";
import findDocumentsByTypes from "../../utils/findDocumentsByTypes";
import { get } from "lodash";
import hasDocumentsLoadError from "../../utils/hasDocumentsLoadError";
import routes from "../../routes";
import uploadDocumentsHelper from "../../utils/uploadDocumentsHelper";
import useFilesLogic from "../../hooks/useFilesLogic";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";
import withClaimDocuments from "../../hoc/withClaimDocuments";

export const UploadId = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim, documents, isLoadingDocuments, query } = props;
  const { files, processFiles, removeFile } = useFilesLogic({
    clearErrors: appLogic.clearErrors,
    catchError: appLogic.catchError,
  });
  const { additionalDoc, showStateId } = query;
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

  const { appErrors, portalFlow } = appLogic;
  const hasLoadingDocumentsError = hasDocumentsLoadError(
    appErrors,
    claim.application_id
  );

  const idDocuments = findDocumentsByTypes(documents, [
    DocumentType.identityVerification,
  ]);

  const handleSave = async () => {
    if (files.isEmpty && idDocuments.length) {
      // Allow user to skip this page if they've previously uploaded documents
      portalFlow.goToNextPage({ claim }, { claim_id: claim.application_id });
      return;
    }

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

    if (success) {
      portalFlow.goToNextPage(
        { claim },
        { claim_id: claim.application_id, uploadedAbsenceId: absence_id }
      );
    }
  };

  const fileErrors = appErrors.items.filter(
    (appErrorInfo) => appErrorInfo.meta && appErrorInfo.meta.file_id
  );

  return (
    <QuestionPage title={t("pages.claimsUploadId.title")} onSave={handleSave}>
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
                "work-visa-link": <a href={routes.external.workVisa} />,
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
                      <a href={routes.external.massgov.identityProof} />
                    ),
                    "puerto-rican-birth-certificate-link": (
                      <a href={routes.external.puertoRicanBirthCertificate} />
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
              aria-valuetext={t(
                "components.withBenefitsApplications.loadingLabel"
              )}
            />
          </div>
        )}

        {!isLoadingDocuments && (
          <FileCardList
            fileErrors={fileErrors}
            tempFiles={files}
            documents={idDocuments}
            onChange={processFiles}
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

UploadId.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    catchError: PropTypes.func.isRequired,
    documents: PropTypes.object.isRequired,
    portalFlow: PropTypes.object.isRequired,
    clearErrors: PropTypes.func.isRequired,
  }).isRequired,
  claim: PropTypes.object.isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
  isLoadingDocuments: PropTypes.bool,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
    showStateId: PropTypes.string,
    additionalDoc: PropTypes.string,
  }),
};

export default withBenefitsApplication(withClaimDocuments(UploadId));
