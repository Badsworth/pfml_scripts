import React, { useState } from "react";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const UploadId = (props) => {
  const { t } = useTranslation();
  const [stateIdFiles, setStateIdFiles] = useState([]);
  const contentContext = props.claim.has_state_id ? "mass" : "other";

  // TODO (CP-396): connect this page to the API file upload endpoint.
  const handleSave = () => {
    props.appLogic.goToNextPage({}, props.query);
  };

  return (
    <QuestionPage title={t("pages.claimsUploadId.title")} onSave={handleSave}>
      <Heading level="2" size="1">
        {t("pages.claimsUploadId.sectionLabel", { context: contentContext })}
      </Heading>
      <Lead>{t("pages.claimsUploadId.lead", { context: contentContext })}</Lead>
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
    </QuestionPage>
  );
};

UploadId.propTypes = {
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.shape({
    goToNextPage: PropTypes.func.isRequired,
    setAppErrors: PropTypes.func.isRequired,
  }).isRequired,
  claim: PropTypes.object.isRequired,
};

export default withClaim(UploadId);
