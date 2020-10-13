import Document, { DocumentType } from "../../models/Document";
import React, { useState } from "react";
import Accordion from "../../components/Accordion";
import AccordionItem from "../../components/AccordionItem";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import Spinner from "../../components/Spinner";
import { Trans } from "react-i18next";
import findDocumentsByType from "../../utils/findDocumentsByType";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";
import withClaimDocuments from "../../hoc/withClaimDocuments";

export const UploadId = (props) => {
  const { t } = useTranslation();
  const [stateIdFiles, setStateIdFiles] = useState([]);
  const hasStateId = props.claim.has_state_id;
  const contentContext = hasStateId ? "mass" : "other";
  const { appLogic, claim, documents, isLoadingDocuments } = props;

  const idDocuments = findDocumentsByType(
    documents,
    DocumentType.identityVerification // TODO (CP-962): Set based on leaveReason
  );

  const handleSave = async () => {
    if (!stateIdFiles.length && idDocuments.length) {
      // Allow user to skip this page if they've previously uploaded documents
      return appLogic.goToNextPage({}, { claim_id: claim.application_id });
    }

    await appLogic.documents.attach(
      claim.application_id,
      stateIdFiles,
      DocumentType.identityVerification // TODO (CP-962): Set based on leaveReason
    );
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

        {isLoadingDocuments && (
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
    claims: PropTypes.object.isRequired,
    documents: PropTypes.object.isRequired,
    goToNextPage: PropTypes.func.isRequired,
    setAppErrors: PropTypes.func.isRequired,
  }).isRequired,
  claim: PropTypes.object.isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
  isLoadingDocuments: PropTypes.bool,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(withClaimDocuments(UploadId));
