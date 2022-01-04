/**
 * Claimants are required to upload different documents for
 * each of the 7 leave reasons that we support. The interface
 * is mostly the same between routes, but the text and the
 * type of document that needs to be uploaded varies.
 *
 * This page uses the url path to determine which document type
 * should be uploaded and what text should be displayed.
 */

import {
  BenefitsApplicationDocument,
  DocumentType,
} from "../../../models/Document";
import withClaimDocuments, {
  WithClaimDocumentsProps,
} from "../../../hoc/withClaimDocuments";
import Accordion from "../../../components/core/Accordion";
import AccordionItem from "../../../components/core/AccordionItem";
import Alert from "../../../components/core/Alert";
import ConditionalContent from "../../../components/ConditionalContent";
import DocumentRequirements from "../../../components/DocumentRequirements";
import FileCardList from "../../../components/FileCardList";
import FileUploadDetails from "../../../components/FileUploadDetails";
import Heading from "../../../components/core/Heading";
import Lead from "../../../components/core/Lead";
import LeaveReason from "../../../models/LeaveReason";
import QuestionPage from "../../../components/QuestionPage";
import React from "react";
import Spinner from "../../../components/core/Spinner";
import { Trans } from "react-i18next";
import findDocumentsByTypes from "../../../utils/findDocumentsByTypes";
import hasDocumentsLoadError from "../../../utils/hasDocumentsLoadError";
import routes from "../../../routes";
import uploadDocumentsHelper from "../../../utils/uploadDocumentsHelper";
import useFilesLogic from "../../../hooks/useFilesLogic";
import { useTranslation } from "../../../locales/i18n";

const uploadRoutes = routes.applications.upload;

/**
 * Map of upload paths to the document type that is
 * uploaded at that path.
 * @type {Object}
 */
const pathsToDocumentTypes = {
  [uploadRoutes.bondingProofOfPlacement]:
    DocumentType.certification[LeaveReason.bonding],
  [uploadRoutes.bondingProofOfBirth]:
    DocumentType.certification[LeaveReason.bonding],
  [uploadRoutes.caringCertification]:
    DocumentType.certification[LeaveReason.care],
  [uploadRoutes.medicalCertification]:
    DocumentType.certification[LeaveReason.medical],
  [uploadRoutes.otherId]: DocumentType.identityVerification,
  [uploadRoutes.pregnancyCertification]:
    DocumentType.certification[LeaveReason.pregnancy],
  [uploadRoutes.stateId]: DocumentType.identityVerification,
};

interface CertificationUploadProps {
  path: string;
}

const CertificationUpload = ({ path }: CertificationUploadProps) => {
  const context = {
    [uploadRoutes.bondingProofOfPlacement]: "bonding_adopt_foster",
    [uploadRoutes.bondingProofOfBirth]: "bonding_newborn",
    [uploadRoutes.caringCertification]: "care",
    [uploadRoutes.medicalCertification]: "medical",
    [uploadRoutes.pregnancyCertification]: "medical",
  }[path];
  const isBondingNewborn = path === uploadRoutes.bondingProofOfBirth;
  const isBonding =
    isBondingNewborn || path === uploadRoutes.bondingProofOfPlacement;

  const { t } = useTranslation();

  return (
    <React.Fragment>
      <Heading level="2" size="1">
        {t("pages.claimsUploadDocumentType.sectionLabel", {
          context: isBonding ? "bonding" : "certification",
        })}
      </Heading>
      <Lead>
        <Trans
          i18nKey="pages.claimsUploadDocumentType.lead"
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
          tOptions={{ context }}
        />
      </Lead>
      <ConditionalContent visible={isBondingNewborn}>
        <ul className="usa-list">
          {t<string, string[]>(
            "pages.claimsUploadDocumentType.leadListNewborn",
            {
              returnObjects: true,
            }
          ).map((listItem, index) => (
            <li key={index}>{listItem}</li>
          ))}
        </ul>
      </ConditionalContent>
      <DocumentRequirements type="certification" />
    </React.Fragment>
  );
};

interface IdentificationUploadProps {
  path: string;
}

const IdentificationUpload = ({ path }: IdentificationUploadProps) => {
  const { t } = useTranslation();
  const isStateId = path === uploadRoutes.stateId;

  return (
    <React.Fragment>
      <Heading level="2" size="1">
        {t("pages.claimsUploadDocumentType.sectionLabel", {
          context: isStateId ? "massId" : "otherId",
        })}
      </Heading>
      <DocumentRequirements type="id" />
      {!isStateId && (
        <div className="border-bottom border-base-light margin-bottom-4 padding-bottom-4">
          <Trans
            i18nKey="pages.claimsUploadDocumentType.otherIdentityDocs"
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
              heading={t("pages.claimsUploadDocumentType.idAccordionHeading")}
            >
              <Trans
                i18nKey="pages.claimsUploadDocumentType.idAccordionContent"
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
    </React.Fragment>
  );
};

interface DocumentUploadProps extends WithClaimDocumentsProps {
  query: {
    claim_id: string;
    additionalDoc?: string;
    absence_id?: string;
    documentType?:
      | "state-id"
      | "other-id"
      | "proof-of-birth"
      | "proof-of-placement"
      | "medical-certification"
      | "pregnancy-medical-certification"
      | "family-member-medical-certification";
  };
}

export const DocumentUpload = (props: DocumentUploadProps) => {
  const { appLogic, documents, isLoadingDocuments, query } = props;
  const { appErrors, portalFlow } = appLogic;
  const { t } = useTranslation();
  const { files, processFiles, removeFile } = useFilesLogic({
    clearErrors: appLogic.clearErrors,
    catchError: appLogic.catchError,
  });
  const [submissionInProgress, setSubmissionInProgress] = React.useState(false);

  const hasLoadingDocumentsError = hasDocumentsLoadError(
    appErrors,
    query.claim_id
  );

  const path = portalFlow.pageRoute;
  const documentType = pathsToDocumentTypes[path];
  const existingDocuments = findDocumentsByTypes<BenefitsApplicationDocument>(
    documents,
    [documentType]
  );

  const isIdUpload = documentType === DocumentType.identityVerification;
  const isCertificationUpload = !isIdUpload;

  // Flag indicating the claimant is uploading additional documents
  // after the application has been completed.
  // If true, the document is immediately marked as received in the CPS,
  // and the user will be navigated back to the claim's status page.
  // The absence_id param is only set when claimant is uploading
  // a document after the application has been completed.
  const isAdditionalDoc = !!query.absence_id;

  const handleSave = async () => {
    if (files.isEmpty && existingDocuments.length) {
      // Allow user to skip this page if they've previously uploaded documents
      portalFlow.goToNextPage(
        { isAdditionalDoc },
        { claim_id: query.claim_id, absence_id: query.absence_id }
      );
      return;
    }
    setSubmissionInProgress(true);
    const uploadPromises = appLogic.documents.attach(
      query.claim_id,
      files.items,
      documentType,
      // indicate whether API should mark document as recieved
      isAdditionalDoc
    );

    const { success } = await uploadDocumentsHelper(
      uploadPromises,
      files,
      removeFile
    );
    setSubmissionInProgress(false);
    if (success) {
      portalFlow.goToNextPage(
        { isAdditionalDoc },
        {
          uploaded_document_type: query.documentType,
          claim_id: query.claim_id,
          absence_id: query.absence_id,
        }
      );
    }
  };

  const fileErrors = appErrors.items.filter(
    (appErrorInfo) => appErrorInfo.meta && appErrorInfo.meta.file_id
  );

  return (
    <QuestionPage
      title={t("pages.claimsUploadDocumentType.title", {
        context: isIdUpload ? "id" : "certification",
      })}
      onSave={handleSave}
    >
      {isCertificationUpload && <CertificationUpload path={path} />}
      {isIdUpload && <IdentificationUpload path={path} />}
      <FileUploadDetails />
      {hasLoadingDocumentsError && (
        <Alert className="margin-bottom-3" noIcon role="alert">
          <Trans
            i18nKey="pages.claimsUploadDocumentType.documentsLoadError"
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
            aria-label={t("components.withClaimDocuments.loadingLabel")}
          />
        </div>
      )}
      {!isLoadingDocuments && (
        <FileCardList
          fileErrors={fileErrors}
          tempFiles={files}
          documents={existingDocuments}
          onChange={processFiles}
          onRemoveTempFile={removeFile}
          disableRemove={submissionInProgress}
          fileHeadingPrefix={t(
            "pages.claimsUploadDocumentType.fileHeadingPrefix"
          )}
          addFirstFileButtonText={t(
            "pages.claimsUploadDocumentType.addFirstFileButton"
          )}
          addAnotherFileButtonText={t(
            "pages.claimsUploadDocumentType.addAnotherFileButton"
          )}
        />
      )}
    </QuestionPage>
  );
};

export default withClaimDocuments(DocumentUpload);

/* eslint-disable require-await */
export async function getStaticPaths() {
  return {
    paths: Object.keys(pathsToDocumentTypes).map((path) => {
      const documentTypeParam = path.replace("/applications/upload/", "");

      return { params: { documentType: documentTypeParam } };
    }),
    fallback: false,
  };
}

export async function getStaticProps() {
  return {
    props: {},
  };
}
