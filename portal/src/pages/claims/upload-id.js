import Document, { DocumentType } from "../../models/Document";
import React, { useState } from "react";
import { get, map } from "lodash";
import Accordion from "../../components/Accordion";
import AccordionItem from "../../components/AccordionItem";
import Alert from "../../components/Alert";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import Spinner from "../../components/Spinner";
import { Trans } from "react-i18next";
import findDocumentsByType from "../../utils/findDocumentsByType";
import hasDocumentsLoadError from "../../utils/hasDocumentsLoadError";
import routes from "../../routes";
import uploadDocumentsHelper from "../../utils/uploadDocumentsHelper";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";
import withClaimDocuments from "../../hoc/withClaimDocuments";

export const UploadId = (props) => {
  const { t } = useTranslation();
  const [stateIdFiles, setStateIdFiles] = useState([]);
  const { appLogic, claim, documents, isLoadingDocuments, query } = props;
  let hasStateId;
  if (query.showStateId === "true") {
    hasStateId = true;
  } else if (query.showStateId === "false") {
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

  const idDocuments = findDocumentsByType(
    documents,
    DocumentType.identityVerification // TODO (CP-962): Set based on leaveReason
  );

  const handleSave = async () => {
    if (!stateIdFiles.length && idDocuments.length) {
      // Allow user to skip this page if they've previously uploaded documents
      return portalFlow.goToNextPage({}, { claim_id: claim.application_id });
    }

    try {
      const uploadPromises = await appLogic.documents.attach(
        claim.application_id,
        map(stateIdFiles, "file"), // extract the "file" object
        DocumentType.identityVerification // TODO (CP-962): set based on leave reason
      );

      const { success } = await uploadDocumentsHelper(
        uploadPromises,
        stateIdFiles,
        setStateIdFiles
      );

      if (success && claim.isCompleted) {
        return portalFlow.goToNextPage(
          { claim },
          { claim_id: claim.application_id, uploadedAbsenceId: absence_id }
        );
      } else if (success) {
        return portalFlow.goToNextPage(
          { claim },
          { claim_id: claim.application_id }
        );
      }
    } catch (error) {
      appLogic.setAppErrors(error);
    }
  };

  return (
    <QuestionPage title={t("pages.claimsUploadId.title")} onSave={handleSave}>
      <div className="measure-6">
        <Heading level="2" size="1">
          {t("pages.claimsUploadId.sectionLabel", { context: contentContext })}
        </Heading>
        <Lead>
          {t("pages.claimsUploadId.lead", { context: contentContext })}
        </Lead>
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
            {t("pages.claimsUploadId.documentsRequestError")}
          </Alert>
        )}

        {isLoadingDocuments && !hasLoadingDocumentsError && (
          <div className="margin-top-8 text-center">
            <Spinner aria-valuetext={t("components.withClaims.loadingLabel")} />
          </div>
        )}

        {!isLoadingDocuments && (
          <FileCardList
            files={stateIdFiles}
            documents={idDocuments}
            setFiles={setStateIdFiles}
            setAppErrors={props.appLogic.setAppErrors}
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
    documents: PropTypes.object.isRequired,
    portalFlow: PropTypes.object.isRequired,
    setAppErrors: PropTypes.func.isRequired,
  }).isRequired,
  claim: PropTypes.object.isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
  isLoadingDocuments: PropTypes.bool,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
    showStateId: PropTypes.string,
  }),
};

export default withClaim(withClaimDocuments(UploadId));
