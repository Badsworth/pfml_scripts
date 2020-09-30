import React, { useState } from "react";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const UploadId = (props) => {
  const { t } = useTranslation();
  const [stateIdFiles, setStateIdFiles] = useState([]);
  const hasStateId = props.claim.has_state_id;
  const contentContext = hasStateId ? "mass" : "other";
  const { appLogic, claim } = props;

  const handleSave = async () => {
    await appLogic.documents.attach(
      claim.application_id,
      stateIdFiles,
      "Identification Proof" // TODO (CP-962): replace this with an enum value
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
              i18nKey="pages.claimsUploadId.validIdDocumentation"
              components={{
                ul: <ul className="usa-list" />,
                li: <li />,
                "identity-proof-link": (
                  <a href={routes.external.massgov.identityProof} />
                ),
                "puerto-rican-birth-certificate-link": (
                  <a href={routes.external.puertoRicanBirthCertificate} />
                ),
                "work-visa-link": <a href={routes.external.workVisa} />,
              }}
            />
          </div>
        )}
        <FileUploadDetails />
        <FileCardList
          files={stateIdFiles}
          setFiles={setStateIdFiles}
          setAppErrors={props.appLogic.setAppErrors}
          fileHeadingPrefix={t("pages.claimsUploadId.fileHeadingPrefix")}
          addFirstFileButtonText={t("pages.claimsUploadId.addFirstFileButton")}
          addAnotherFileButtonText={t(
            "pages.claimsUploadId.addAnotherFileButton"
          )}
        />
      </div>
    </QuestionPage>
  );
};

UploadId.propTypes = {
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.shape({
    claims: PropTypes.object.isRequired,
    documents: PropTypes.object.isRequired,
    goToNextPage: PropTypes.func.isRequired,
    setAppErrors: PropTypes.func.isRequired,
  }).isRequired,
  claim: PropTypes.object.isRequired,
};

export default withClaim(UploadId);
