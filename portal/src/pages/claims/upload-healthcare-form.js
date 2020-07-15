import React, { useState } from "react";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

const UploadHealthcareForm = (props) => {
  const { t } = useTranslation();
  const [files, setFiles] = useState([]);

  // @todo: CP-396 connect this page to the API file upload endpoint.
  const handleSave = () => {
    props.appLogic.goToNextPage(null, props.query);
  };

  return (
    <QuestionPage
      title={t("pages.claimsUploadHealthcareForm.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsUploadHealthcareForm.sectionLabel")}
      </Heading>
      <Lead>{t("pages.claimsUploadHealthcareForm.lead")}</Lead>
      <FileUploadDetails />
      <FileCardList
        files={files}
        setFiles={setFiles}
        setAppErrors={props.appLogic.setAppErrors}
        fileHeadingPrefix={t(
          "pages.claimsUploadHealthcareForm.fileHeadingPrefix"
        )}
        addFirstFileButtonText={t(
          "pages.claimsUploadHealthcareForm.addFirstFileButtonText"
        )}
        addAnotherFileButtonText={t(
          "pages.claimsUploadHealthcareForm.addAnotherFileButtonText"
        )}
      />
    </QuestionPage>
  );
};

UploadHealthcareForm.propTypes = {
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(UploadHealthcareForm);
