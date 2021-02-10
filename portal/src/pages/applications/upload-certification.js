import Claim, { ReasonQualifier } from "../../models/Claim";
import Document, { DocumentType } from "../../models/Document";
import Alert from "../../components/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import Spinner from "../../components/Spinner";
import TempFileCollection from "../../models/TempFileCollection";
import { Trans } from "react-i18next";
import findDocumentsByTypes from "../../utils/findDocumentsByTypes";
import findKeyByValue from "../../utils/findKeyByValue";
import { get } from "lodash";
import hasDocumentsLoadError from "../../utils/hasDocumentsLoadError";
import routes from "../../routes";
import uploadDocumentsHelper from "../../utils/uploadDocumentsHelper";
import useTempFileCollection from "../../hooks/useTempFileCollection";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";
import withClaimDocuments from "../../hoc/withClaimDocuments";

export const UploadCertification = (props) => {
  const { appLogic, claim, documents, isLoadingDocuments, query } = props;
  const { t } = useTranslation();
  const claimReason = claim.leave_details.reason;
  const claimReasonQualifier = claim.leave_details.reason_qualifier;

  const { appErrors, portalFlow } = appLogic;
  const { tempFiles, addTempFiles, removeTempFile } = useTempFileCollection(
    new TempFileCollection(),
    {
      clearErrors: appLogic.clearErrors,
    }
  );
  const hasLoadingDocumentsError = hasDocumentsLoadError(
    appErrors,
    claim.application_id
  );

  const conditionalContext = {
    [LeaveReason.bonding]: {
      [ReasonQualifier.newBorn]: "bonding_newborn",
      [ReasonQualifier.adoption]: "bonding_adopt_foster",
      [ReasonQualifier.fosterCare]: "bonding_adopt_foster",
    },
    [LeaveReason.medical]: "medical",
  };
  let leadTextContext;
  switch (claimReason) {
    case LeaveReason.medical:
      leadTextContext = conditionalContext[claimReason];
      break;
    case LeaveReason.bonding:
      leadTextContext = conditionalContext[claimReason][claimReasonQualifier];
      break;
  }

  const certificationDocuments = findDocumentsByTypes(
    documents,
    [DocumentType.medicalCertification] // TODO (CP-962): Set based on leaveReason
  );

  const handleSave = async () => {
    if (tempFiles.isEmpty && certificationDocuments.length) {
      // Allow user to skip this page if they've previously uploaded documents
      portalFlow.goToNextPage({ claim }, { claim_id: claim.application_id });
      return;
    }

    const uploadPromises = appLogic.documents.attach(
      claim.application_id,
      tempFiles.items,
      DocumentType.medicalCertification, // TODO (CP-962): set based on leave reason
      query.additionalDoc === "true"
    );

    const { success } = await uploadDocumentsHelper(
      uploadPromises,
      tempFiles,
      removeTempFile
    );
    if (success) {
      const absence_id = get(claim, "fineos_absence_id");
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
    <QuestionPage
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
            "mail-fax-instructions-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.mailFaxInstructions}
              />
            ),
            "healthcare-provider-form-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.healthcareProviderForm}
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
        <ul className="usa-list">
          {t("pages.claimsUploadCertification.leadListNewborn", {
            returnObjects: true,
          }).map((listItem, index) => (
            <li key={index}>{listItem}</li>
          ))}
        </ul>
      </ConditionalContent>
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
          <Spinner aria-valuetext={t("components.withClaims.loadingLabel")} />
        </div>
      )}
      {!isLoadingDocuments && (
        <FileCardList
          fileErrors={fileErrors}
          tempFiles={tempFiles}
          documents={certificationDocuments}
          onAddTempFiles={addTempFiles}
          onRemoveTempFile={removeTempFile}
          onInvalidFilesError={appLogic.catchError}
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

UploadCertification.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    catchError: PropTypes.func.isRequired,
    documents: PropTypes.object.isRequired,
    portalFlow: PropTypes.object.isRequired,
    clearErrors: PropTypes.func.isRequired,
  }).isRequired,
  claim: PropTypes.instanceOf(Claim),
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
  isLoadingDocuments: PropTypes.bool,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
    additionalDoc: PropTypes.string,
  }),
};

export default withClaim(withClaimDocuments(UploadCertification));
