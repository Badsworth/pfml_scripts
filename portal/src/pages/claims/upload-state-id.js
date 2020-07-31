import React, { useState } from "react";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

const UploadStateId = (props) => {
  const { t } = useTranslation();
  const [stateIdFiles, setStateIdFiles] = useState([]);

  // @todo: CP-396 connect this page to the API file upload endpoint.
  const handleSave = () => {
    props.appLogic.goToNextPage({}, props.query);
  };

  return (
    <QuestionPage
      title={t("pages.claimsUploadStateId.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsUploadStateId.sectionLabel")}
      </Heading>
      <Lead>{t("pages.claimsUploadStateId.lead")}</Lead>
      <FileUploadDetails />
      <FileCardList
        files={stateIdFiles}
        setFiles={setStateIdFiles}
        setAppErrors={props.appLogic.setAppErrors}
        fileHeadingPrefix={t("pages.claimsUploadStateId.fileHeadingPrefix")}
        addFirstFileButtonText={t(
          "pages.claimsUploadStateId.addFirstFileButton"
        )}
        addAnotherFileButtonText={t(
          "pages.claimsUploadStateId.addAnotherFileButton"
        )}
      />
    </QuestionPage>
  );
};

UploadStateId.propTypes = {
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.shape({
    goToNextPage: PropTypes.func.isRequired,
    setAppErrors: PropTypes.func.isRequired,
  }).isRequired,
};

export default withClaim(UploadStateId);
