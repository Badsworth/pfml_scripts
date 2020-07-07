import React, { useState } from "react";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { useTranslation } from "../../locales/i18n";

const UploadOtherId = (props) => {
  const { t } = useTranslation();
  const [otherIdFiles, setOtherIdFiles] = useState([]);
  const documentList = t("pages.claimsUploadOtherId.documentList", {
    returnObjects: true,
  });

  // @todo: CP-396 connect this page to the API file upload endpoint.
  const handleSave = () => {
    props.appLogic.goToNextPage({}, props.query);
  };

  return (
    <QuestionPage
      title={t("pages.claimsUploadOtherId.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsUploadOtherId.sectionLabel")}
      </Heading>
      <Lead>{t("pages.claimsUploadOtherId.lead")}</Lead>
      <ul className="usa-list">
        {documentList.map((listItem, index) => (
          <li key={index}>{listItem}</li>
        ))}
      </ul>
      <FileUploadDetails />
      <FileCardList
        files={otherIdFiles}
        setFiles={setOtherIdFiles}
        setAppErrors={props.appLogic.setAppErrors}
        fileHeadingPrefix={t("pages.claimsUploadOtherId.fileHeadingPrefix")}
        addFirstFileButtonText={t(
          "pages.claimsUploadOtherId.addFirstFileButtonText"
        )}
        addAnotherFileButtonText={t(
          "pages.claimsUploadOtherId.addAnotherFileButtonText"
        )}
      />
    </QuestionPage>
  );
};

UploadOtherId.propTypes = {
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.shape({
    goToNextPage: PropTypes.func.isRequired,
    setAppErrors: PropTypes.func.isRequired,
  }).isRequired,
};

export default UploadOtherId;
